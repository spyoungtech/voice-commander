import json
import os
import pathlib
import typing
from pathlib import Path
from typing import Any
from typing import Self

import json5

from ._utils import get_listener
from ._utils import get_logger
from .triggers import TriggerBase


logger = get_logger()


def load_profile(filepath: str | pathlib.Path) -> 'Profile':
    with open(filepath) as f:
        data = json5.load(f)
    return Profile.from_dict(data)


class Profile:
    def __init__(self, profile_name: str, triggers: list[TriggerBase] | None = None) -> None:
        self.name = profile_name
        self.triggers: list[TriggerBase] = triggers or []

    def add_trigger(self, trigger: TriggerBase) -> Self:
        self.triggers.append(trigger)
        return self

    def to_dict(self) -> dict[str, Any]:
        from .schema import CURRENT_SCHEMA_VERSION

        return {
            'configuration': {
                'profile_name': self.name,
                'schema_version': CURRENT_SCHEMA_VERSION,
                'triggers': [trigger.to_dict() for trigger in self.triggers],
            }
        }

    def activate(self) -> Self:
        for trigger in self.triggers:
            trigger.install_hook()
        return self

    def deactivate(self) -> None:
        logger.info('Deactivating profile')
        for trigger in self.triggers:
            trigger.uninstall_hook()
        listener = get_listener()
        listener.stop()

    def dump_json(self, file_handle: typing.TextIO, indent: int = 4) -> None:
        json.dump(self.to_dict(), file_handle, indent=indent)

    def dumps_json(self, indent: int = 4) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save_json(
        self,
        dirname: Path | str | None = None,
        filename: Path | str | None = None,
        create_dir: bool = True,
        overwrite: bool = False,
    ) -> None:
        if dirname is None:
            dirname = os.path.expanduser('~/.voice_commander/profiles')
        if filename is None:
            filename = f'{self.name}.profile.json'

        dirname = pathlib.Path(dirname).absolute()
        filename = pathlib.Path(filename)

        if not dirname.exists():
            if create_dir is True:
                os.makedirs(dirname)
            else:
                raise NotADirectoryError(f'dirname {dirname} does not exist.')
        if not dirname.is_dir():
            raise NotADirectoryError(f'dirname {dirname} is not a directory (may be a file)')

        fp = dirname / filename
        if fp.exists():
            if fp.is_dir():
                raise IsADirectoryError(f'{fp} already exists and is a directory, not a file')
            if overwrite is False:
                raise FileExistsError('File already exists but overwrite parameter is False')
        with open(fp, 'w') as outfile:
            self.dump_json(outfile)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        triggers_data = data.get('triggers', [])
        triggers: list[TriggerBase] = []
        for trigger_data in triggers_data:
            t = TriggerBase.from_dict(trigger_data.get('trigger_config', {}))
            triggers.append(t)
        name = data['profile_name']
        return cls(profile_name=name, triggers=triggers)
