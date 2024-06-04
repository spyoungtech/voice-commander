from __future__ import annotations

from typing import Self

from ._utils import get_listener
from .profile import Profile


class ApplicationState:
    def __init__(self) -> None:
        self._active_profile_name: str | None = None
        self._all_profiles: dict[str, Profile] = {'default': Profile('default')}
        self._listener = get_listener()

    @property
    def active_profile_name(self) -> str | None:
        return self._active_profile_name

    @active_profile_name.setter
    def active_profile_name(self, new_profile_name: str | None) -> None:
        if self._active_profile_name is not None:
            active_profile = self._all_profiles[self._active_profile_name]
            active_profile.deactivate()
        self._active_profile_name = new_profile_name
        if new_profile_name is not None:
            new_profile = self._all_profiles[new_profile_name]
            new_profile.activate()

    @property
    def active_profile(self) -> None | Profile:
        if self._active_profile_name is not None:
            return self._all_profiles.get(self._active_profile_name, None)
        else:
            return None

    def add_profile(self, profile_name: str, profile: Profile) -> Self:
        assert profile_name not in self._all_profiles, 'Profile name already exists'
        self._all_profiles[profile_name] = profile
        return self

    def delete_profile(self, profile_name: str) -> None:
        assert profile_name in self._all_profiles, 'Profile name does not exist'
        del self._all_profiles[profile_name]

    @property
    def available_profile_names(self) -> list[str]:
        return list(self._all_profiles)
