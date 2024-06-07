from __future__ import annotations

import abc
from typing import Any
from typing import NotRequired
from typing import Self
from typing import Type
from typing import TypedDict
from typing import TypeVar
from typing import Unpack

import ahk.exceptions
from ahk import TitleMatchMode

from voice_commander._utils import get_ahk

_condition_registry: dict[str, Type['ConditionBase']] = {}
T_Condition = TypeVar('T_Condition', bound='ConditionBase')


def restore_condition(condition_data: dict[str, Any]) -> 'ConditionBase':
    condition_type = condition_data.get('condition_type')
    if condition_type not in _condition_registry:
        raise ValueError(f'unknown condition type: {condition_type!r}')
    klass = _condition_registry[condition_type]
    return klass.from_dict(condition_data)


class ConditionBase:
    @classmethod
    def fqn(cls) -> str:
        return f'{cls.__module__}.{cls.__qualname__}'

    @classmethod
    def __init_subclass__(cls: Type[T_Condition], **kwargs: Any) -> None:
        fqn = cls.fqn()
        assert fqn not in _condition_registry, f'cannot register class {cls!r} with fqn {fqn!r} which is already in use'
        _condition_registry[fqn] = cls
        super().__init_subclass__(**kwargs)

    @abc.abstractmethod
    def check(self) -> bool: ...

    def to_dict(self) -> dict[str, Any]:
        return {'condition_type': self.fqn()}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        condition_type = d.get('condition_type', None)
        assert condition_type == cls.fqn(), f'invalid condition type: {condition_type!r}'
        kwargs = d.get('condition_config', {})
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
        return cls(*args, **kwargs)


class AHKWindowExists(ConditionBase):
    """
    Uses AutoHotkey to check if a given window exists

    Availability: Windows
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
        self.win_get_kwargs = win_get_kwargs

    def check(self) -> bool:
        engine = get_ahk()
        try:
            return engine.win_exists(**self.win_get_kwargs, blocking=False).result()
        except ahk.exceptions.WindowNotFoundException:
            return False

    def to_dict(self) -> dict[str, Any]:
        return {'condition_type': self.fqn(), 'condition_config': self.win_get_kwargs}


class AHKWindowIsActive(ConditionBase):
    """
    Uses AutoHotkey to determine if a window is currently active

    Availability: Windows
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
        self.win_get_kwargs = win_get_kwargs

    def check(self) -> bool:
        engine = get_ahk()
        try:
            return engine.win_is_active(**self.win_get_kwargs, blocking=False).result()
        except ahk.exceptions.WindowNotFoundException:
            return False

    def to_dict(self) -> dict[str, Any]:
        return {'condition_type': self.fqn(), 'condition_config': self.win_get_kwargs}
