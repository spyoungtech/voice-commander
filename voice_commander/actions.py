from __future__ import annotations

import abc
import os.path
import time
import warnings
from typing import Any
from typing import NotRequired
from typing import Self
from typing import Type
from typing import TypedDict
from typing import TypeVar
from typing import Unpack

from ahk import TitleMatchMode

from ._utils import get_ahk
from ._utils import get_logger

winsound: Any = None
try:
    import winsound
except ImportError:
    pass


_action_registry: dict[str, Type['ActionBase']] = {}
T_Action = TypeVar('T_Action', bound='ActionBase')

logger = get_logger()


def restore_action(action_data: dict[str, Any]) -> 'ActionBase':
    action_type = action_data.get('action_type')
    if action_type not in _action_registry:
        raise ValueError(f'unknown action {action_type!r}')
    klass = _action_registry[action_type]
    return klass.from_dict(action_data)


class ActionBase:
    @classmethod
    def fqn(cls) -> str:
        return f'{cls.__module__}.{cls.__qualname__}'

    @classmethod
    def __init_subclass__(cls: Type[T_Action], **kwargs: Any) -> None:
        fqn = cls.fqn()
        assert fqn not in _action_registry, f'cannot register class {cls!r} with fqn {fqn!r} which is already in use'
        _action_registry[fqn] = cls
        super().__init_subclass__(**kwargs)

    @abc.abstractmethod
    def perform(self) -> None: ...

    @abc.abstractmethod
    def to_dict(self) -> dict[str, Any]:
        return NotImplemented

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        # TODO: support variadic parameters, like in TriggerBase.from_dict
        action_type = d.get('action_type', None)
        assert action_type == cls.fqn(), f'action type {action_type!r} was unexpected. Was expecting {cls.fqn()!r}'
        kwargs = d.get('action_config', {})
        return cls(**kwargs)


class AHKSendAction(ActionBase):
    """
    Send inputs using AutoHotkey
    """

    class ConfigDict(TypedDict):
        send_string: str

    def __init__(self, send_string: str):
        """
        :param send_string: the keys to send - uses AutoHotkey's `Send <https://www.autohotkey.com/docs/v1/lib/Send.htm>`_ function
        """
        self.send_string: str = send_string

    def perform(self) -> None:
        engine = get_ahk()
        engine.send(self.send_string)

    def to_dict(self) -> dict[str, Any]:
        return {'action_type': self.fqn(), 'action_config': {'send_string': self.send_string}}


class AHKPressAction(ActionBase):
    """
    Press (and release) a single key.
    Adds small delay between key down and key up, useful for making sure games register inputs.
    """

    class ConfigDict(TypedDict):
        key: str

    def __init__(self, key: str):
        """

        :param key: the key to press. Do not include braces for special keys.
        """
        self.key: str = key

    def perform(self) -> None:
        engine = get_ahk()
        engine.send(f'{{Blind}}{{{self.key} DOWN}}', blocking=False)
        time.sleep(0.1)
        engine.send(f'{{Blind}}{{{self.key} UP}}', blocking=False)
        time.sleep(0.1)

    def to_dict(self) -> dict[str, Any]:
        return {'action_type': self.fqn(), 'action_config': {'key': self.key}}


class WinSoundAction(ActionBase):
    """
    Play a sound (wav file)
    """

    class ConfigDict(TypedDict):
        sound_file_path: str

    def __init__(self, sound_file_path: str):
        """

        :param sound_file_path: the path to the sound file. Must be .wav format.
        """
        if winsound is None:
            warnings.warn(
                message='winsound module is not available. WinSoundAction will fail when triggered.',
                category=RuntimeWarning,
                stacklevel=2,
            )
        sound_file_path = os.path.abspath(sound_file_path)
        self.sound_file_path: str = sound_file_path
        if winsound is None:
            self._flags = None
        else:
            self._flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NOSTOP

    def perform(self) -> None:
        if winsound is None:
            raise RuntimeError('winsound module is not available')
        winsound.PlaySound(self.sound_file_path, self._flags)

    def to_dict(self) -> dict[str, Any]:
        return {'action_type': self.fqn(), 'action_config': {'sound_file_path': self.sound_file_path}}


class AHKMakeWindowActiveAction(ActionBase):
    """
    Make a window active, ensuring it has focus
    """

    class ConfigDict(TypedDict):
        title: NotRequired[str]
        text: NotRequired[str]
        exclude_title: NotRequired[str]
        exclude_text: NotRequired[str]
        title_match_mode: NotRequired[TitleMatchMode]
        detect_hidden_windows: NotRequired[bool]

    def __init__(self, **win_get_kwargs: Unpack[ConfigDict]):
        """

        :param win_get_kwargs:
        """
        self._win_get_kwargs = win_get_kwargs

    def perform(self) -> None:
        engine = get_ahk()
        win = engine.win_get(**self._win_get_kwargs)
        assert win is not None, f'Could not find window with parameters {self._win_get_kwargs!r}'
        win.activate()

    def to_dict(self) -> dict[str, Any]:
        return {'action_type': self.fqn(), 'action_config': self._win_get_kwargs}


class PauseAction(ActionBase):
    """
    Sleeps for specified time
    """

    class ConfigDict(TypedDict):
        seconds: int | float

    def __init__(self, seconds: float | int):
        """

        :param seconds: time in seconds to sleep
        """
        self.seconds: float | int = seconds

    def perform(self) -> None:
        time.sleep(self.seconds)

    def to_dict(self) -> dict[str, Any]:
        return {'action_type': self.fqn(), 'action_config': {'seconds': self.seconds}}
