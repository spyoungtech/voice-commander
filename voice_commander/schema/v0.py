from __future__ import annotations

from typing import Any
from typing import Literal
from typing import TypeAlias
from typing import Union

import pydantic
from pydantic import BaseModel
from pydantic import field_validator

from voice_commander.actions import _action_registry
from voice_commander.actions import ActionBase
from voice_commander.actions import AHKMakeWindowActiveAction
from voice_commander.actions import AHKPressAction
from voice_commander.actions import AHKSendAction
from voice_commander.actions import PauseAction
from voice_commander.actions import restore_action
from voice_commander.conditions import AHKWindowExists
from voice_commander.conditions import AHKWindowIsActive
from voice_commander.conditions import ConditionBase
from voice_commander.conditions import restore_condition
from voice_commander.profile import Profile
from voice_commander.triggers import _trigger_registry
from voice_commander.triggers import HotkeyTrigger
from voice_commander.triggers import JoystickAxisTrigger
from voice_commander.triggers import JoystickButtonTrigger
from voice_commander.triggers import restore_trigger
from voice_commander.triggers import TriggerBase
from voice_commander.triggers import VoiceTrigger


class ConditionSchema(BaseModel):
    condition_type: str
    condition_config: dict[str, Any]

    def to_condition(self) -> ConditionBase:
        return restore_condition(self.dict())


class AHKWindowExistsConditionSchema(BaseModel):
    condition_type: Literal['voice_commander.conditions.AHKWindowExists']
    condition_config: AHKWindowExists.ConfigDict

    def to_condition(self) -> AHKWindowExists:
        return AHKWindowExists.from_dict(self.dict())


class AHKWindowIsActiveConditionSchema(BaseModel):
    condition_type: Literal['voice_commander.conditions.AHKWindowIsActive']
    condition_config: AHKWindowIsActive.ConfigDict

    def to_condition(self) -> AHKWindowIsActive:
        return AHKWindowIsActive.from_dict(self.dict())


T_Conditions: TypeAlias = Union[ConditionSchema, AHKWindowExistsConditionSchema, AHKWindowIsActiveConditionSchema]


class AHKSendActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.AHKSendAction']
    action_config: AHKSendAction.ConfigDict
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_action(self) -> AHKSendAction:
        return AHKSendAction.from_dict(self.dict())


class AHKPressActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.AHKPressAction']
    action_config: AHKPressAction.ConfigDict
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_action(self) -> AHKPressAction:
        return AHKPressAction.from_dict(self.dict())


class AHKMakeWindowActiveActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.AHKMakeWindowActiveAction']
    action_config: AHKMakeWindowActiveAction.ConfigDict
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_action(self) -> AHKMakeWindowActiveAction:
        return AHKMakeWindowActiveAction.from_dict(self.dict())


class PauseActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.PauseAction']
    action_config: PauseAction.ConfigDict
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_action(self) -> PauseAction:
        return PauseAction.from_dict(self.dict())


class ActionSchema(BaseModel):
    action_type: str
    action_config: dict[str, Any]
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    @field_validator('action_type')
    @classmethod
    def action_type_must_exist(cls, v: str) -> str:
        if v not in _action_registry:
            raise ValueError(f'Action type {v!r} does not exist. Must be one of {list(_action_registry.keys())!r}')
        return v

    def to_action(self) -> ActionBase:
        return restore_action(self.dict())


T_Actions: TypeAlias = Union[
    AHKSendActionSchema,
    AHKPressActionSchema,
    AHKMakeWindowActiveActionSchema,
    PauseActionSchema,
    ActionSchema,
]


class HotkeyTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.HotkeyTrigger']
    trigger_config: HotkeyTrigger.ConfigDict
    actions: list[T_Actions]
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_trigger(self) -> HotkeyTrigger:
        return HotkeyTrigger.from_dict(self.dict())


class JoystickAxisTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.JoystickAxisTrigger']
    trigger_config: JoystickAxisTrigger.ConfigDict
    actions: list[T_Actions]
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_trigger(self) -> JoystickAxisTrigger:
        return JoystickAxisTrigger.from_dict(self.dict())


class JoystickButtonTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.JoystickButtonTrigger']
    trigger_config: JoystickButtonTrigger.ConfigDict
    actions: list[T_Actions]
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_trigger(self) -> JoystickButtonTrigger:
        return JoystickButtonTrigger.from_dict(self.dict())


class VoiceTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.VoiceTrigger']
    trigger_config: VoiceTrigger.ConfigDict
    actions: list[T_Actions]
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    def to_trigger(self) -> VoiceTrigger:
        return VoiceTrigger.from_dict(self.dict())


class TriggerSchema(BaseModel):
    trigger_type: str
    trigger_config: dict[str, Any]
    actions: list[T_Actions]
    conditions: list[T_Conditions] = pydantic.Field(default_factory=list)

    @field_validator('trigger_type')
    @classmethod
    def trigger_type_must_exist(cls, v: str) -> str:
        if v not in _trigger_registry:
            raise ValueError(f'Trigger type {v!r} does not exist. Must be one of {list(_trigger_registry.keys())!r}')
        return v

    def to_trigger(self) -> TriggerBase:
        return restore_trigger(self.dict())


T_Triggers: TypeAlias = Union[
    HotkeyTriggerSchema,
    JoystickAxisTriggerSchema,
    JoystickButtonTriggerSchema,
    VoiceTriggerSchema,
    TriggerSchema,
]


class ProfileConfig(BaseModel):
    schema_version: Literal['0'] = '0'
    profile_name: str
    triggers: list[T_Triggers]

    def to_profile(self) -> Profile:
        p = Profile(profile_name=self.profile_name)
        for trigger_def in self.triggers:
            p.add_trigger(trigger_def.to_trigger())
        return p
