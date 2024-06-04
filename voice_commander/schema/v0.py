from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import field_validator

from voice_commander.actions import _action_registry
from voice_commander.actions import ActionBase
from voice_commander.actions import AHKMakeWindowActiveAction
from voice_commander.actions import AHKPressAction
from voice_commander.actions import AHKSendAction
from voice_commander.actions import PauseAction
from voice_commander.actions import restore_action
from voice_commander.profile import Profile
from voice_commander.triggers import _trigger_registry
from voice_commander.triggers import HotkeyTrigger
from voice_commander.triggers import JoystickAxisTrigger
from voice_commander.triggers import JoystickButtonTrigger
from voice_commander.triggers import restore_trigger
from voice_commander.triggers import TriggerBase
from voice_commander.triggers import VoiceTrigger


class AHKSendActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.AHKSendAction']
    action_config: AHKSendAction.ConfigDict


class AHKPressActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.AHKPressAction']
    action_config: AHKPressAction.ConfigDict


class AHKMakeWindowActiveActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.AHKMakeWindowActiveAction']
    action_config: AHKMakeWindowActiveAction.ConfigDict


class PauseActionSchema(BaseModel):
    action_type: Literal['voice_commander.actions.PauseAction']
    action_config: PauseAction.ConfigDict


class ActionSchema(BaseModel):
    action_type: str
    action_config: dict[str, Any]

    @field_validator('action_type')
    @classmethod
    def action_type_must_exist(cls, v: str) -> str:
        if v not in _action_registry:
            raise ValueError(f'Action type {v!r} does not exist. Must be one of {list(_action_registry.keys())!r}')
        return v

    def to_action(self) -> ActionBase:
        return restore_action(self.dict())


class HotkeyTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.HotkeyTrigger']
    trigger_config: HotkeyTrigger.ConfigDict

    def to_trigger(self) -> HotkeyTrigger:
        return HotkeyTrigger.from_dict(self.dict())


class JoystickAxisTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.JoystickAxisTrigger']
    trigger_config: JoystickAxisTrigger.ConfigDict

    def to_trigger(self) -> JoystickAxisTrigger:
        return JoystickAxisTrigger.from_dict(self.dict())


class JoystickButtonTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.JoystickButtonTrigger']
    trigger_config: JoystickButtonTrigger.ConfigDict

    def to_trigger(self) -> JoystickButtonTrigger:
        return JoystickButtonTrigger.from_dict(self.dict())


class VoiceTriggerSchema(BaseModel):
    trigger_type: Literal['voice_commander.triggers.VoiceTrigger']
    trigger_config: VoiceTrigger.ConfigDict

    def to_trigger(self) -> VoiceTrigger:
        return VoiceTrigger.from_dict(self.dict())


class TriggerSchema(BaseModel):
    trigger_type: str
    actions: list[AHKSendActionSchema | AHKPressActionSchema | AHKMakeWindowActiveActionSchema | ActionSchema]
    trigger_config: dict[str, Any]

    @field_validator('trigger_type')
    @classmethod
    def trigger_type_must_exist(cls, v: str) -> str:
        if v not in _trigger_registry:
            raise ValueError(f'Trigger type {v!r} does not exist. Must be one of {list(_trigger_registry.keys())!r}')
        return v

    def to_trigger(self) -> TriggerBase:
        return restore_trigger(self.dict())


class ProfileConfig(BaseModel):
    schema_version: Literal['0'] = '0'
    profile_name: str
    triggers: list[TriggerSchema]

    def to_profile(self) -> Profile:
        p = Profile(profile_name=self.profile_name)
        for trigger_def in self.triggers:
            p.add_trigger(trigger_def.to_trigger())
        return p
