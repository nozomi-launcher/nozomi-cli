import os
import nozomi.cli.commands.remove_shortcut.error_codes as err
from collections import namedtuple
from nozomi.cli.console_colors import *
from nozomi.lib.command import BaseCommand
from nozomi.lib.vdf_file import VdfFile
from nozomi.lib.steam_helper import find_steam_user_id, find_image_by_name, generate_shortcut_vdf_app_id
from nozomi.lib.constants import STEAM_USERDATA_PATH

__tuple__ = namedtuple('tuple', 'app_id, error_code')


class Command(BaseCommand):
    def __init__(self):
        self.__command_name = 'remove_shortcut'

    def get_command_str(self) -> str:
        return self.__command_name

    def register_options(self, subparsers) -> None:
        add_shortcut_command = subparsers.add_parser(self.__command_name, help='removes an executable shortcut to steam')
        add_shortcut_command.add_argument(
            '--app-name',
            dest='app_name',
            metavar='<name>',
            required=False,
            help='The name of the shortcut'
        )
        add_shortcut_command.add_argument(
            '--exe-path',
            dest='exe_path',
            metavar='<path/to/executable>',
            required=False,
            help='The full path to the executable'
        )
        add_shortcut_command.add_argument(
            '--app-id',
            dest='app_id',
            metavar='<app_id>',
            required=False,
            help='The (unsigned) app id of the shortcut'
        )
        add_shortcut_command.add_argument(
            '--dry-run',
            dest='dry_run',
            action='store_true',
            required=False,
            help='Performs a dry run'
        )

    def command(self, args) -> int:
        if args.dry_run:
            print_yellow('dry run, not actually modifying steam')
        if args.app_id is not None:
            result = remove_non_steam_game_by_app_id(
                app_id=args.app_id,
                dry_run=args.dry_run
            )
        elif args.app_name is not None and args.exe_path is not None:
            result = remove_non_steam_game(
                app_name=args.app_name,
                exe_path=args.exe_path,
                dry_run=args.dry_run
            )
        else:
            print_red('Either the app-id or both app-name and exe-path are required')
            return err.ERROR_MISSING_REQUIRED_ARGUMENTS

        if result != 0:
            return result

        update_indices(dry_run=args.dry_run)
        return 0


def remove_non_steam_game_by_app_id(
        app_id: str,
        dry_run: bool = False
        ) -> int:

    print_green(f'Removing {app_id} to steam...')

    user_id = find_steam_user_id()

    if user_id is None:
        print_red('could not find steam user id')
        return err.ERROR_STEAM_USER_NOT_FOUND
    print(f'found steam user id: {user_id}')

    shortcuts_vdf_path = os.path.expanduser(os.path.join(STEAM_USERDATA_PATH, user_id, 'config', 'shortcuts.vdf'))

    shortcuts_vdf = VdfFile(shortcuts_vdf_path, binary=True, create_if_not_exists=True)

    return find_and_remove_shortcut(shortcuts_vdf, app_id, user_id, dry_run=dry_run)


def remove_non_steam_game(
        app_name: str,
        exe_path: str,
        dry_run: bool = False
        ) -> int:

    expanded_exe_path = os.path.expanduser(exe_path)

    print_green(f'Removing {expanded_exe_path} to steam...')

    if not os.path.isabs(expanded_exe_path):
        print_red(f'path {expanded_exe_path} is not a full path')
        return err.ERROR_PATH_NOT_ABSOLUTE
    user_id = find_steam_user_id()

    if user_id is None:
        print_red('could not find steam user id')
        return err.ERROR_STEAM_USER_NOT_FOUND
    print(f'found steam user id: {user_id}')

    shortcuts_vdf_path = os.path.expanduser(os.path.join(STEAM_USERDATA_PATH, user_id, 'config', 'shortcuts.vdf'))

    shortcuts_vdf = VdfFile(shortcuts_vdf_path, binary=True, create_if_not_exists=True)

    signed_app_id = generate_shortcut_vdf_app_id(f'{app_name}{expanded_exe_path}')

    app_ids_found = get_app_ids(shortcuts_vdf)

    if app_ids_found is None:
        return err.ERROR_NO_SHORTCUT_TO_REMOVE

    return find_and_remove_shortcut(shortcuts_vdf, signed_app_id, user_id, dry_run=dry_run, app_id_is_signed=True)


def remove_art_work(
        user_id: str,
        unsigned_app_id: str,
        dry_run: bool = False,
        ):
    grid_dir = os.path.expanduser(os.path.join(STEAM_USERDATA_PATH, user_id, 'config', 'grid'))
    if not os.path.exists(grid_dir):
        print_yellow(f'grid directory {grid_dir} does not exist, nothing to remove')
        return

    images_to_remove = [
        f'{unsigned_app_id}_hero',
        f'{unsigned_app_id}_logo',
        unsigned_app_id,
        f'{unsigned_app_id}p',
        f'{unsigned_app_id}_icon',
    ]

    for image in images_to_remove:
        image_to_remove = find_image_by_name(image, grid_dir)
        if image_to_remove is not None:
            print_green(f'removing {image_to_remove} image...')
            if not dry_run:
                os.remove(image_to_remove)
            else:
                print_yellow(f'dry run, not actually removing {image_to_remove} image')

    return


def get_app_ids(
        shortcuts_vdf: VdfFile,
        ) -> dict | None:

    if 'shortcuts' not in shortcuts_vdf.data:
        print_red('shortcuts key not found in shortcuts.vdf, nothing to remove')
        return None

    app_ids_found = {}

    for shortcuts in shortcuts_vdf.data.get_all_for('shortcuts'):
        indices = list(shortcuts.iterkeys())
        for index in indices:
            shortcut = shortcuts[index]
            if 'appid' in shortcut:
                app_ids_found[str(shortcut['appid'])] = index
            if 'AppId' in shortcut:
                app_ids_found[str(shortcut['AppId'])] = index

    return app_ids_found


def find_and_remove_shortcut(
        shortcuts_vdf: VdfFile,
        app_id: str,
        user_id: str,
        dry_run: bool = False,
        app_id_is_signed: bool = False) -> int:

    if not app_id_is_signed:
        signed_app_id = str(int(app_id) - 2 ** 32)
        unsigned_app_id = app_id
    else:
        signed_app_id = app_id
        unsigned_app_id = str(int(app_id) + 2 ** 32)

    app_ids_found = get_app_ids(shortcuts_vdf)

    if app_ids_found is None:
        return err.ERROR_NO_SHORTCUT_TO_REMOVE

    print_blue('original shortcuts_vdf: ' + str(shortcuts_vdf.data))

    if signed_app_id in app_ids_found:
        print_cyan('summary of shortcut to remove:')
        print(f'app id: {unsigned_app_id}')
        print(f'app name: {shortcuts_vdf.data['shortcuts'][app_ids_found[signed_app_id]]["AppName"]}')
        print(f'exe path: {shortcuts_vdf.data["shortcuts"][app_ids_found[signed_app_id]]["Exe"]}')
        del shortcuts_vdf.data['shortcuts'][app_ids_found[signed_app_id]]
    else:
        print_red(f'app id {signed_app_id} not found in shortcuts.vdf')
        return err.ERROR_NO_SHORTCUT_TO_REMOVE

    print_cyan('modified shortcuts_vdf.data ' + str(shortcuts_vdf.data))

    if not dry_run:
        shortcuts_vdf.save()
    else:
        print_yellow('dry run, not modifying shortcuts.vdf')

    remove_art_work(user_id, unsigned_app_id, dry_run=dry_run)

    return 0


def update_indices(dry_run: bool):
    user_id = find_steam_user_id()

    shortcuts_vdf_path = os.path.expanduser(os.path.join(STEAM_USERDATA_PATH, user_id, 'config', 'shortcuts.vdf'))

    shortcuts_vdf = VdfFile(shortcuts_vdf_path, binary=True, create_if_not_exists=True)

    print_blue(f'updating {shortcuts_vdf_path} so shortcuts are in sequential order')

    for shortcuts in shortcuts_vdf.data.get_all_for('shortcuts'):
        cache_shortcuts = []
        indices = list(shortcuts.iterkeys())
        for index in indices:
            cache_shortcuts.append(shortcuts[index])
            del shortcuts[index]
        real_index = 0
        for cached_shortcut in cache_shortcuts:
            shortcuts[str(real_index)] = cached_shortcut
            real_index += 1

    if not dry_run:
        shortcuts_vdf.save()
    else:
        print_yellow('dry run, not modifying shortcuts.vdf')
