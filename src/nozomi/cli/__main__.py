#!/usr/bin/env python3

import sys
import argparse

from nozomi.lib.command import BaseCommand

from commands import info, add_shortcut, remove_shortcut, install
import importlib.metadata


def main():
    if len(sys.argv) == 1:
        sys.argv.append('--help')

    parser = argparse.ArgumentParser(description="All in one steam game manager")
    parser.add_argument('--version', action='store_true', help='Print the version of nozomi')
    subparsers = parser.add_subparsers(metavar="[command]", dest="command", help="Available commands")
    commands: list[BaseCommand] = [
        info.Command(),
        add_shortcut.Command(),
        install.Command(),
        remove_shortcut.Command(),
    ]

    command_lookup = {}
    for command in commands:
        command.register_options(subparsers)
        command_lookup[command.get_command_str()] = command

    args = parser.parse_args()

    if args.version:
        print_version_and_exit()

    result = command_lookup[args.command].command(args)
    sys.exit(result)


def print_version_and_exit():
    version = importlib.metadata.version('nozomi')
    print(f'nozomi-cli {version}')
    sys.exit(0)


if __name__ == '__main__':
    main()
