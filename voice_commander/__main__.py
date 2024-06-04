from __future__ import annotations

import argparse
import logging
import sys

from voice_commander._utils import get_logger
from voice_commander.profiles import load_profile
from voice_commander.profiles import load_profile_from_name

logger = get_logger()

if __name__ == '__main__':
    parser = argparse.ArgumentParser('voice_commander')
    subparsers = parser.add_subparsers(help='sub-commands', dest='subcommand')
    run_profile_subparser = subparsers.add_parser('run_profile', help='Run a profile from a file')
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
