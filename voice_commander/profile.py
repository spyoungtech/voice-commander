from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import typing
from pathlib import Path
from typing import Any
from typing import Self

import json5

from ._utils import get_listener
from ._utils import get_logger
from .triggers import TriggerBase


logger = get_logger()


def _get_default_profile_path() -> str:
    return os.path.expanduser('~/.voice_commander/profiles')


def load_profile(filepath: str | pathlib.Path, filetype: typing.Literal['yaml', 'json'] | None = None) -> 'Profile':
    from .schema import ProfileSchema

    if filetype == 'yaml' or (filetype is None and (str(filepath).endswith('.yml') or str(filepath).endswith('.yaml'))):
        import yaml

        with open(filepath) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            return ProfileSchema.parse_obj(data).to_profile()
    with open(filepath) as f:
        data = json5.load(f)
    return ProfileSchema.parse_obj(data).to_profile()


def load_profile_from_name(profile_name: str) -> 'Profile':
    """
    Loads a profile by name from the default profiles directory ("~/.voice_commander/profiles")

    :param profile_name: the name of the profile
    """
    for filename in (f'{profile_name}.vcp.json', f'{profile_name}.vcp.yaml'):

        fp = os.path.join(_get_default_profile_path(), filename)
        if not os.path.isfile(fp):
            continue
        else:
            break
    else:
        raise FileNotFoundError(
            f'Profile with name {profile_name!r} could not be found in {_get_default_profile_path()}'
        )

    return load_profile(fp)


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
        logger.info(f'Deactivating profile {self.name!r}')
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
            filename = f'{self.name}.vcp.json'

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

    def save_yaml(
        self,
        dirname: Path | str | None = None,
        filename: Path | str | None = None,
        create_dir: bool = True,
        overwrite: bool = False,
    ) -> None:
        import yaml

        if dirname is None:
            dirname = os.path.expanduser('~/.voice_commander/profiles')
        if filename is None:
            filename = f'{self.name}.vcp.yaml'

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
            yaml.dump(self.to_dict(), outfile, sort_keys=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        triggers_data = data.get('triggers', [])
        triggers: list[TriggerBase] = []
        for trigger_data in triggers_data:
            t = TriggerBase.from_dict(trigger_data.get('trigger_config', {}))
            triggers.append(t)
        name = data['profile_name']
        return cls(profile_name=name, triggers=triggers)

    def __enter__(self) -> Self:
        self.activate()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.deactivate()

    def run(self) -> None:
        print(f'Running profile {self.name!r}. Press ctrl+c to stop', flush=True, file=sys.stderr)
        with self:
            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                print('KeyboardInterrupt received. Stopping.', file=sys.stderr, flush=True)
        return None
