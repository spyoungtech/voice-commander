from __future__ import annotations

import abc
import enum
import logging
import queue
from threading import Thread
from typing import Any
from typing import Literal
from typing import NotRequired
from typing import Self
from typing import Type
from typing import TypedDict
from typing import TypeVar

from ._utils import get_ahk
from ._utils import get_listener
from ._utils import get_logger
from .actions import ActionBase
from .actions import restore_action
from .conditions import ConditionBase
from .conditions import restore_condition
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

    def to_dict(self) -> dict[str, Any]:
        return {
            'trigger_type': self.fqn(),
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
    class ConfigDict(TypedDict):
        hotkey: str

    def __init__(self, hotkey: str):
        super().__init__()
        self.hotkey = hotkey

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {'trigger_config': {'hotkey': self.hotkey}}

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
    class ConfigDict(TypedDict):
        joystick_index: int | str
        joystick_button: str

    def __init__(self, joystick_index: int | str, joystick_button: str):
        self.joystick_index = joystick_index
        self.joystick_button = joystick_button
        super().__init__(hotkey=f'{joystick_index}Joy{joystick_button}')

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'trigger_config': {'joystick_index': self.joystick_index, 'joystick_button': self.joystick_button}
        }


class AxisTriggerMode(enum.IntEnum):
    VALUE_BETWEEN = 1  # Triggers when axis value is within the specified range. Resets when the value falls outside the specified range.
    VALUE_ABOVE = 2  # Triggers when the axis value is greater than the specified value. Resets when the axis value is less than the specified value.
    VALUE_BELOW = 3  # Triggers when the axis value is less than the specified value. Resets when the axis value is greater than the specified value.


class JoystickAxisTrigger(TriggerBase):
    class ConfigDict(TypedDict):
        joystick_index: int
        axis_name: Literal['X', 'Y', 'Z', 'V', 'U', 'R']
        trigger_mode: AxisTriggerMode | Literal[1, 2, 3]
        trigger_value: int | float | tuple[int | float, int | float]
        polling_frequency: NotRequired[int]

    def __init__(
        self,
        joystick_index: int,
        axis_name: str,
        trigger_mode: AxisTriggerMode | int,
        trigger_value: int | float | tuple[int | float, int | float],
        polling_frequency: int = 30,
    ):
        super().__init__()
        self.joystick_index = joystick_index
        self.axis_name = (axis_name,)
        self.trigger_mode = trigger_mode
        self.trigger_value = (trigger_value,)
        self.polling_frequency = polling_frequency

    def _listen_joystick(self) -> None: ...

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'trigger_config': {
                'joystick_index': self.joystick_index,
                'axis_name': self.axis_name,
                'trigger_mode': int(self.trigger_mode),
                'trigger_value': self.trigger_value,
                'polling_frequency': self.polling_frequency,
            },
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        action_type = d.get('trigger_type', None)
        assert action_type == cls.fqn()
        kwargs = d.get('properties', {})
        trigger_mode_int = kwargs.pop('trigger_mode', None)
        match trigger_mode_int:
            case 1:
                kwargs['trigger_mode'] = AxisTriggerMode.VALUE_BETWEEN
            case 2:
                kwargs['trigger_mode'] = AxisTriggerMode.VALUE_ABOVE
            case 3:
                kwargs['trigger_mode'] = AxisTriggerMode.VALUE_BELOW
            case _:
                raise ValueError(f'invalid trigger mode: {trigger_mode_int}')
        instance = cls(**kwargs)
        for action_data in d.get('actions', []):
            action = ActionBase.from_dict(action_data)
            instance.add_action(action)
        return instance

    def install_hook(self) -> None:
        raise NotImplementedError()

    def uninstall_hook(self) -> None:
        raise NotImplementedError()


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

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {'trigger_config': {'*trigger_phrases': self.trigger_phrases}}

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
