from __future__ import annotations

from pydantic import BaseModel

from ..profile import Profile
from .v0 import ProfileConfig as ProfileConfigV0

CURRENT_SCHEMA_VERSION = '0'


class ProfileSchema(BaseModel):
    configuration: ProfileConfigV0

    def to_profile(self) -> Profile:
        return self.configuration.to_profile()


__all__ = ['ProfileSchema', 'CURRENT_SCHEMA_VERSION']
