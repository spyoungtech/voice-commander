from __future__ import annotations

import abc
import enum
import logging
import queue
import time
from threading import Thread
from typing import Any
from typing import Literal
from typing import NotRequired
from typing import Self
from typing import Type
from typing import TypedDict
from typing import TypeVar

from ._utils import get_ahk
from ._utils import get_joy_listener
from ._utils import get_listener
from ._utils import get_logger
from .actions import ActionBase
from .actions import restore_action
from .conditions import ConditionBase
from .conditions import restore_condition
from .joy_listener import JoyListener
from .voice_listener import Listener

T_Trigger = TypeVar('T_Trigger', bound='TriggerBase')
_trigger_registry: dict[str, Type['TriggerBase']] = {}

logger = get_logger()


def restore_trigger(trigger_data: dict[str, Any]) -> 'TriggerBase':
    trigger_type = trigger_data.get('trigger_type')
    if trigger_type not in _trigger_registry:
        raise ValueError(f'unknown trigger type: {trigger_type!r}')
    klass = _trigger_registry[trigger_type]
    return klass.from_dict(trigger_data)


class TriggerBase:
    def __init__(self) -> None:
        self.actions: list[ActionBase] = []
        self.conditions: list[ConditionBase] = []

    def add_condition(self, condition: ConditionBase) -> Self:
        self.conditions.append(condition)
        return self

    def add_actions(self, *actions: ActionBase) -> Self:
        for action in actions:
            self.actions.append(action)
        return self

    def add_action(self, action: ActionBase) -> Self:
        self.actions.append(action)
        return self

    @classmethod
    def fqn(cls) -> str:
        return f'{cls.__module__}.{cls.__qualname__}'

    @classmethod
    def __init_subclass__(cls: Type[T_Trigger], **kwargs: Any) -> None:
        fqn = cls.fqn()
        assert fqn not in _trigger_registry, f'cannot register class {cls!r} with fqn {fqn!r} which is already in use'
        _trigger_registry[fqn] = cls
        super().__init_subclass__(**kwargs)

    @abc.abstractmethod
    def _get_config(self) -> Any: ...

    def to_dict(self) -> dict[str, Any]:
        return {
            'trigger_type': self.fqn(),
            'trigger_config': self._get_config(),
            'actions': [action.to_dict() for action in self.actions],
            'conditions': [cond.to_dict() for cond in self.conditions],
        }

    @abc.abstractmethod
    def install_hook(self) -> None: ...
    @abc.abstractmethod
    def uninstall_hook(self) -> None: ...

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        action_type = d.get('trigger_type', None)
        assert action_type == cls.fqn()
        kwargs = d.get('trigger_config', {})
        args: list[Any] | None = None
        variadic_argname: str | None = None
        for argname in kwargs:
            if argname.startswith('*'):
                if args is None:
                    args = kwargs[argname]
                    variadic_argname = argname
                    assert isinstance(args, list)
                else:
                    raise TypeError(f'Multiple variadic properties provided: second variadic: {argname!r}')
        if args is None:
            args = []
        else:
            kwargs.pop(variadic_argname)
        instance = cls(*args, **kwargs)

        for action_data in d.get('actions', []):
            action = restore_action(action_data)
            instance.add_action(action)
        for condition_data in d.get('conditions', []):
            condition = restore_condition(condition_data)
            instance.add_condition(condition)
        return instance

    def check_conditions(self) -> bool:
        return all(cond.check() for cond in self.conditions)

    def on_trigger(self) -> None:
        logger.debug('Checking conditions before performing actions')
        if self.check_conditions():
            logger.info('Conditions check passed. Performing actions')
            for action in self.actions:
                logger.debug('Checking action condition')
                if action.check_conditions():
                    logger.info('Performing action')
                    action.perform()
                else:
                    logger.info('Skipping action due to unmet condition')
            logger.info('Actions')
        else:
            logger.info('Trigger skipped due to unmet condition(s)')


class HotkeyTrigger(TriggerBase):
    """
    Uses AutoHotkey hotkeys to trigger actions.

    Availability: Windows
    """

    class ConfigDict(TypedDict):
        hotkey: str

    def __init__(self, hotkey: str):
        """
        :param hotkey: the trigger hotkey -- same syntax as `AutoHotkey hotkeys <https://www.autohotkey.com/docs/v1/Hotkeys.htm>`_
        """
        super().__init__()
        self.hotkey = hotkey

    def _get_config(self) -> ConfigDict:
        return {'hotkey': self.hotkey}

    def install_hook(self) -> None:
        ahk = get_ahk()
        ahk.add_hotkey(self.hotkey, callback=self.on_trigger)
        try:
            ahk.start_hotkeys()
        except Exception:
            pass

    def uninstall_hook(self) -> None:
        ahk = get_ahk()
        ahk.remove_hotkey(self.hotkey)
        try:
            ahk.stop_hotkeys()
        except Exception:
            pass


class JoystickButtonTrigger(HotkeyTrigger):
    """
    Like :py:class:`voice_commander.triggers.HotkeyTrigger` but with a convenient constructor for defining joystick button hotkeys.

    Availability: Windows
    """

    class ConfigDict(TypedDict):
        joystick_index: int | str
        joystick_button: str

    def __init__(self, joystick_index: int | str, joystick_button: str):
        """

        :param joystick_index: the index of the joystick device (per AutoHotkey indices)
        :param joystick_button: the button number (between 1 and 32)
        """
        self.joystick_index = joystick_index
        self.joystick_button = joystick_button
        super().__init__(hotkey=f'{joystick_index}Joy{joystick_button}')

    def _get_config(self) -> ConfigDict:  # type: ignore[override]
        return {'joystick_index': self.joystick_index, 'joystick_button': self.joystick_button}


class AxisTriggerMode(enum.IntEnum):
    """
    Available trigger modes for joystick axis trigger.
    """

    VALUE_BETWEEN = 1  # Triggers when axis value is within the specified range. Resets when the value falls outside the specified range.
    VALUE_ABOVE = 2  # Triggers when the axis value is greater than the specified value. Resets when the axis value is less than the specified value.
    VALUE_BELOW = 3  # Triggers when the axis value is less than the specified value. Resets when the axis value is greater than the specified value.
    VALUE_EQUALS = 4  # Triggers when the axis value is **exactly** the specified value


class JoystickAxisTrigger(TriggerBase):
    """
    Uses AutoHotkey to monitor joystick axis values and trigger according to specified parameters

    Availability: Windows
    """

    class ConfigDict(TypedDict):
        joystick_index: int
        axis_name: Literal['X', 'Y', 'Z', 'V', 'U', 'R']
        trigger_mode: AxisTriggerMode
        trigger_value: int | float | tuple[int | float, int | float]
        polling_frequency: NotRequired[int]

    def __init__(
        self,
        axis_name: str,
        trigger_mode: AxisTriggerMode | int,
        trigger_value: int | float | tuple[int | float, int | float],
        joystick_index: int,
        polling_frequency: int = 30,
    ):
        """

        :param axis_name: The name of the axis to monitor: X, Y, Z, R, U, V, or POV
        :param trigger_mode: one of :py:class:`~voice_commander.triggers.AxisTriggerMode` - controls the logic of trigger gates
        :param trigger_value: the axis value trigger threshold(s). When using ``VALUE_BETWEEN`` mode, use a tuple to specify the lower and upper threshold bounds.
        :param joystick_index: the index of the joystick to monitor
        :param polling_frequency: how frequently to check axis value (the higher this value is, the lower the delay between checks)
        """
        super().__init__()
        assert axis_name in ['X', 'Y', 'Z', 'V', 'U', 'R']
        assert int(trigger_mode) in (1, 2, 3, 4)
        if trigger_mode == 1:
            trigger_mode = AxisTriggerMode.VALUE_BETWEEN
        elif trigger_mode == 2:
            trigger_mode = AxisTriggerMode.VALUE_ABOVE
        elif trigger_mode == 3:
            trigger_mode = AxisTriggerMode.VALUE_BELOW
        elif trigger_mode == 4:
            trigger_mode = AxisTriggerMode.VALUE_EQUALS
        else:
            raise ValueError(f"Invalid trigger mode: {trigger_mode!r}")
        self.joystick_index = joystick_index
        self.axis_name: str = axis_name
        self.trigger_mode: AxisTriggerMode = trigger_mode
        self.trigger_value = trigger_value
        self.polling_frequency = polling_frequency
        self._joy_listener: JoyListener = get_joy_listener()
        self._listener_thread: Thread | None = None
        self._running: bool = False
        self._awaiting_reset: bool = True

    def _evaluate_trigger(self, current_value: int | float, last_value: int | float) -> None:
        if self.trigger_mode == AxisTriggerMode.VALUE_BELOW:
            assert isinstance(self.trigger_value, (int, float))
            if current_value > self.trigger_value:
                if self._awaiting_reset:
                    self._awaiting_reset = False
            elif current_value < self.trigger_value:
                if not self._awaiting_reset:
                    self._awaiting_reset = True
                    self.on_trigger()

        elif self.trigger_mode == AxisTriggerMode.VALUE_ABOVE:
            assert isinstance(self.trigger_value, (int, float))

            if current_value < self.trigger_value:
                if self._awaiting_reset:
                    self._awaiting_reset = False
            elif current_value > self.trigger_value:
                if not self._awaiting_reset:
                    self._awaiting_reset = True
                    self.on_trigger()
        elif self.trigger_mode == AxisTriggerMode.VALUE_BETWEEN:
            assert isinstance(self.trigger_value, tuple)
            lower_bound, upper_bound = self.trigger_value
            if lower_bound < current_value < upper_bound:
                if not self._awaiting_reset:
                    self._awaiting_reset = True
                    self.on_trigger()
            else:
                if self._awaiting_reset:
                    self._awaiting_reset = False

        elif self.trigger_mode == AxisTriggerMode.VALUE_EQUALS:
            assert isinstance(self.trigger_value, (int, float))
            if current_value == self.trigger_value:
                if not self._awaiting_reset:
                    self._awaiting_reset = True
                    self.on_trigger()
            else:
                if self._awaiting_reset:
                    self._awaiting_reset = False

    def _listen_joystick(self) -> None:
        last_value = None
        start_attempts = 0
        while True:
            try:
                self._joy_listener.get_joystick_axis_value(axis=self.axis_name, joystick_index=self.joystick_index)
                break
            except Exception:
                if start_attempts >= 5:
                    raise
                start_attempts += 1
                time.sleep(0.2)

        while True:
            if not self._running:
                break
            time.sleep(1 / self.polling_frequency)
            current_value = self._joy_listener.get_joystick_axis_value(
                axis=self.axis_name, joystick_index=self.joystick_index
            )
            if last_value is None:
                last_value = current_value
            self._evaluate_trigger(current_value, last_value)

    def _get_config(self) -> ConfigDict:
        return {
            'joystick_index': self.joystick_index,
            'axis_name': self.axis_name,  # type: ignore[typeddict-item]
            'trigger_mode': int(self.trigger_mode),  # type: ignore[typeddict-item]
            'trigger_value': self.trigger_value,
            'polling_frequency': self.polling_frequency,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        action_type = d.get('trigger_type', None)
        assert action_type == cls.fqn()
        kwargs = d.get('properties', {})
        trigger_mode_int = kwargs.pop('trigger_mode', None)
        match trigger_mode_int:
            case AxisTriggerMode():
                kwargs['trigger_value'] = trigger_mode_int
            case 1:
                kwargs['trigger_mode'] = AxisTriggerMode.VALUE_BETWEEN
            case 2:
                kwargs['trigger_mode'] = AxisTriggerMode.VALUE_ABOVE
            case 3:
                kwargs['trigger_mode'] = AxisTriggerMode.VALUE_BELOW
            case 4:
                kwargs['trigger_mode'] = AxisTriggerMode.VALUE_EQUALS
            case _:
                raise ValueError(f'invalid trigger mode: {trigger_mode_int!r}')
        instance = cls(**kwargs)
        for action_data in d.get('actions', []):
            action = ActionBase.from_dict(action_data)
            instance.add_action(action)
        return instance

    def install_hook(self) -> None:
        assert self._listener_thread is None
        assert self._running is False
        self._running = True
        self._joy_listener.start()
        self._listener_thread = Thread(target=self._listen_joystick)
        self._listener_thread.start()

    def uninstall_hook(self) -> None:
        assert self._running is True
        assert self._listener_thread is not None
        self._running = False
        self._listener_thread.join()
        self._listener_thread = None
        self._joy_listener.stop()  # XXX: hmm...


class VoiceTrigger(TriggerBase):
    """
    Trigger on spoken voice commands. You can add multiple trigger phrases at once.
    """

    ConfigDict = TypedDict('ConfigDict', {'*trigger_phrases': list[str]})

    def __init__(self, *trigger_phrases: str):
        super().__init__()
        self.trigger_phrases: list[str] = [phrase.lower() for phrase in trigger_phrases]
        self._listener: Listener = get_listener()
        self._match_queue: queue.Queue[str] = self._listener.add_trigger_phrases(self.trigger_phrases)
        self._thread: Thread | None = None

    def _wait_for_trigger(self) -> None:
        while True:
            msg = self._match_queue.get()
            if msg == 'STOP':
                self._match_queue.task_done()
                break
            logging.info(f'received voice trigger for msg: {msg}')
            self.on_trigger()
            self._match_queue.task_done()
        return None

    def _get_config(self) -> dict[str, Any]:
        return {'*trigger_phrases': self.trigger_phrases}

    def install_hook(self) -> None:
        assert self._thread is None
        self._thread = Thread(target=self._wait_for_trigger)
        self._thread.start()
        self._listener.start()

    def uninstall_hook(self) -> None:
        assert self._thread is not None
        self._match_queue.put_nowait('STOP')
        self._thread.join()
        self._thread = None
        self._listener.stop()
