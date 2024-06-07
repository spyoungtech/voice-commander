from __future__ import annotations

import argparse
import logging
import sys
import time
from collections.abc import Callable

from voice_commander._utils import get_ahk
from voice_commander._utils import get_joystick_axis_or_pov
from voice_commander._utils import get_logger
from voice_commander.profile import load_profile
from voice_commander.profile import load_profile_from_name

logger = get_logger()


def _button_monitor() -> None:
    ahk = get_ahk(use_global=False)

    def make_callback(index: str | int, button: int) -> Callable[..., None]:
        def inner() -> None:
            print(f'You pressed button {button!r} on joystick with index {index!r}')

        return inner

    for button in range(1, 33):
        ahk.add_hotkey(f'Joy{button}', callback=make_callback('', button))

    for joystick in range(1, 17):
        for button in range(1, 33):
            ahk.add_hotkey(f'{joystick}Joy{button}', callback=make_callback(joystick, button))
    ahk.start_hotkeys()
    print('Press any joystick button to show its information! Press Ctrl-C to stop.')
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print('Stopping!')
        ahk.stop_hotkeys()
        return


def _axis_monitor() -> None:
    print('Move any joystick axis (more than 30%) to display axis information. Press Ctrl-C to stop.')
    try:
        while True:
            joystick_index, axis, value = get_joystick_axis_or_pov()
            print(f'You moved the {axis!r} axis on joystick {joystick_index!r} (current value {value!r})')
    except KeyboardInterrupt:
        raise SystemExit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('voice_commander')
    subparsers = parser.add_subparsers(help='sub-commands', dest='subcommand')
    run_profile_subparser = subparsers.add_parser('run-profile', help='Run a profile from a file')
    subparsers.add_parser('joy-button-info')
    subparsers.add_parser('joy-axis-info')
    profile_group = run_profile_subparser.add_mutually_exclusive_group()
    profile_group.add_argument(
        '--profile-name', help='The name of the profile. Looks in the default profiles directory'
    )
    profile_group.add_argument('--profile-file', help='The absolute path to the profile file')
    run_profile_subparser.add_argument('--log-level', choices=('DEBUG', 'INFO', 'WARNING', 'ERROR'), default='INFO')
    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
        raise SystemExit(1)
    if args.subcommand == 'run_profile':
        log_level = getattr(logging, args.log_level, logging.INFO)
        logger.setLevel(log_level)
        if args.profile_name is None and args.profile_file is None:
            print('ERROR: Profile must be provided', file=sys.stderr, flush=True)
            run_profile_subparser.print_help()
            raise SystemExit(1)
        if args.profile_name is not None:
            profile = load_profile_from_name(args.profile_name)
        else:
            profile = load_profile(args.profile_file)
        profile.run()
        raise SystemExit(0)
    elif args.subcommand == 'joy-button-info':
        _button_monitor()
    elif args.subcommand == 'joy-axis-info':
        _axis_monitor()
