import os
import shutil
from argparse import Namespace
import nozomi.cli.commands.add_shortcut.error_codes as err
from collections import namedtuple
from nozomi.cli.console_colors import *
from nozomi.lib.command import BaseCommand
from nozomi.lib.vdf_file import VdfFile
from nozomi.lib.steam_helper import find_steam_user_id, generate_shortcut_vdf_app_id
from nozomi.lib.constants import STEAM_USERDATA_PATH, \
    STEAM_COMPAT_TOOLS_PATH, \
    STEAM_CONFIG_VDF_PATH

__tuple__ = namedtuple('tuple', 'app_id, error_code')

from vdf import VDFDict


class Command(BaseCommand):
    def __init__(self):
        self.__command_name = 'add_shortcut'

    def get_command_str(self) -> str:
        return self.__command_name

    def register_options(self, subparsers) -> None:
        add_shortcut_command = subparsers.add_parser(self.__command_name, help='adds an executable shortcut to steam')
        add_shortcut_command.add_argument(
            '--app-name',
            dest='app_name',
            metavar='<name>',
            required=True,
            help='(Required) The name of the shortcut')
        add_shortcut_command.add_argument(
            '--exe-path',
            dest='exe_path',
            metavar='<path/to/executable>',
            required=True,
            help='(Required) The full path to the executable')
        add_shortcut_command.add_argument(
            '--compat-tool',
            dest='compat_tool',
            metavar='<compat_tool>',
            required=False,
            help='The name of the compatability tool to use')
        add_shortcut_command.add_argument(
            '--hero',
            dest='hero',
            metavar='<path/to/hero/image>',
            required=False,
            help='The path to the hero image'
        )
        add_shortcut_command.add_argument(
            '--logo',
            dest='logo',
            metavar='<path/to/logo/image>',
            required=False,
            help='The path to the logo image'
        )
        add_shortcut_command.add_argument(
            '--tenfoot',
            dest='tenfoot',
            metavar='<path/to/tenfoot/image>',
            required=False,
            help='The path to the tenfoot image'
        )
        add_shortcut_command.add_argument(
            '--boxart',
            dest='boxart',
            metavar='<path/to/boxart/image>',
            required=False,
            help='The path to the boxart image'
        )
        add_shortcut_command.add_argument(
            '--icon',
            dest='icon',
            metavar='<path/to/icon/image>',
            required=False,
            help='The path to the icon image'
        )
        add_shortcut_command.add_argument(
            '--launch-options',
            dest='launch_options',
            metavar='<launch options>',
            required=False,
            help='The launch options for the shortcut'
        )
        add_shortcut_command.add_argument(
            '--dry-run',
            dest='dry_run',
            action='store_true',
            required=False,
            help='Performs a dry run'
        )

    def command(self, args: Namespace) -> int:
        return add_non_steam_game(
            app_name=args.app_name,
            exe_path=args.exe_path,
            compat_tool=args.compat_tool,
            hero=args.hero,
            logo=args.logo,
            tenfoot=args.tenfoot,
            boxart=args.boxart,
            icon=args.icon,
            launch_options=args.launch_options,
            dry_run=args.dry_run
        )


def add_non_steam_game(
        app_name: str,
        exe_path: str,
        compat_tool: str | None,
        hero: str | None,
        logo: str | None,
        tenfoot: str | None,
        boxart: str | None,
        icon: str | None,
        launch_options: str | None,
        dry_run: bool = False
        ) -> int:
    if dry_run:
        print_yellow('Dry run, not actually modifying steam')

    expanded_exe_path = os.path.expanduser(exe_path)

    print_green(f'Adding {expanded_exe_path} to steam...')

    if not os.path.isabs(expanded_exe_path):
        print_red(f'Path {expanded_exe_path} is not a full path')
        return err.ERROR_PATH_NOT_ABSOLUTE
    user_id = find_steam_user_id()

    if user_id is None:
        print_red('Could not find steam user id')
        return err.ERROR_STEAM_USER_NOT_FOUND
    print(f'Found steam user id: {user_id}')

    [app_id, error_code] = modify_user_config_vdf(
        user_id=user_id,
        app_name=app_name,
        expanded_exe_path=expanded_exe_path,
        icon=icon,
        launch_options=launch_options,
        dry_run=dry_run
    )

    if error_code != 0:
        return error_code

    result = set_compat_tool(app_id=app_id, compat_tool=compat_tool, dry_run=dry_run)
    if result != 0:
        return result

    result = set_art_work(
        user_id=user_id,
        app_id=app_id,
        hero=hero,
        logo=logo,
        tenfoot=tenfoot,
        boxart=boxart,
        icon=icon,
        dry_run=dry_run)
    if result != 0:
        return result

    return 0


def modify_user_config_vdf(
        user_id: str,
        app_name: str,
        expanded_exe_path: str,
        icon: str | None,
        launch_options: str | None,
        dry_run: bool = False
        ) -> __tuple__:
    shortcuts_vdf_path = os.path.expanduser(os.path.join(STEAM_USERDATA_PATH, user_id, 'config', 'shortcuts.vdf'))

    shortcuts_vdf = VdfFile(shortcuts_vdf_path, binary=True, create_if_not_exists=True)

    signed_app_id = generate_shortcut_vdf_app_id(f'{app_name}{os.path.basename(expanded_exe_path)}')
    unsigned_app_id = str(int(signed_app_id) + 2**32)

    print_cyan('Summary of shortcut to add:')
    print(f'app id: {unsigned_app_id}')
    print(f'app name: {app_name}')
    print(f'exe path: {expanded_exe_path}')
    print(f'icon: {icon}')
    print(f'launch options: {launch_options}')

    if 'shortcuts' not in shortcuts_vdf.data:
        shortcuts_vdf.data['shortcuts'] = VDFDict()

    print_blue('Original shortcuts_vdf: ' + str(shortcuts_vdf.data))

    indices_found = []
    app_ids_found = []

    for shortcuts in shortcuts_vdf.data.get_all_for('shortcuts'):
        indices = list(shortcuts.iterkeys())
        for index in indices:
            shortcut = shortcuts[index]
            indices_found.append(index)
            if 'appid' in shortcut:
                app_ids_found.append(str(shortcut['appid']))
            if 'AppId' in shortcut:
                app_ids_found.append(str(shortcut['AppId']))

    if signed_app_id in app_ids_found:
        print_red(f'App id {signed_app_id} already exists, skipping...')
        return __tuple__(app_id=None, error_code=err.ERROR_APP_ID_ALREADY_EXISTS)

    number_index = 0
    if len(indices_found) > 0:
        # find the first unused index in indices_found
        while str(number_index) in indices_found:
            number_index += 1

    index = str(number_index)
    if index not in shortcuts_vdf.data['shortcuts']:
        shortcuts_vdf.data['shortcuts'][index] = VDFDict()

    if icon is not None:
        grid_dir = get_grid_dir(user_id)
        local_icon = os.path.join(grid_dir, f'{unsigned_app_id}_icon{os.path.splitext(icon)[1]}')
    else:
        local_icon = ''

    shortcuts_vdf.data['shortcuts'][index]['appid'] = signed_app_id
    shortcuts_vdf.data['shortcuts'][index]['AppName'] = app_name
    shortcuts_vdf.data['shortcuts'][index]['Exe'] = expanded_exe_path
    shortcuts_vdf.data['shortcuts'][index]['StartDir'] = f'"{os.path.dirname(expanded_exe_path)}"'
    shortcuts_vdf.data['shortcuts'][index]['icon'] = local_icon
    shortcuts_vdf.data['shortcuts'][index]['ShortcutPath'] = ''
    shortcuts_vdf.data['shortcuts'][index]['LaunchOptions'] = launch_options if launch_options is not None else ''
    shortcuts_vdf.data['shortcuts'][index]['IsHidden'] = 0
    shortcuts_vdf.data['shortcuts'][index]['AllowDesktopConfig'] = 1
    shortcuts_vdf.data['shortcuts'][index]['AllowOverlay'] = 1
    shortcuts_vdf.data['shortcuts'][index]['OpenVR'] = 0
    shortcuts_vdf.data['shortcuts'][index]['Devkit'] = 0
    shortcuts_vdf.data['shortcuts'][index]['DevkitGameID'] = ''
    shortcuts_vdf.data['shortcuts'][index]['DevKitOverrideAppID'] = ''
    shortcuts_vdf.data['shortcuts'][index]['LastPlayTime'] = 0
    shortcuts_vdf.data['shortcuts'][index]['FlatpakAppId'] = ''
    shortcuts_vdf.data['shortcuts'][index]['tags'] = VDFDict()

    print_cyan('Modified shortcuts_vdf.data ' + str(shortcuts_vdf.data))

    if not dry_run:
        shortcuts_vdf.save()
    else:
        print_yellow('Dry run, not modifying shortcuts.vdf')

    # convert to unsigned int since that's what users expect
    return __tuple__(app_id=unsigned_app_id, error_code=0)


def set_compat_tool(app_id: str, compat_tool: str | None, dry_run: bool = False) -> int:
    if compat_tool is None:
        print_yellow('No compat tool specified, skipping...')
        return 0

    compat_tool_path = os.path.expanduser(os.path.join(STEAM_COMPAT_TOOLS_PATH, compat_tool))

    if not os.path.exists(compat_tool_path):
        print_red(f'Compat tool {compat_tool} does not exist')
        return err.ERROR_COMPAT_TOOL_DOES_NOT_EXIST

    print_cyan(f'Setting compat tool to {compat_tool}')
    config_vdf = VdfFile(STEAM_CONFIG_VDF_PATH)

    config_dict = config_vdf.data
    properties = ['InstallConfigStore', 'Software', 'Valve', 'Steam', 'CompatToolMapping']
    prop_explored = []

    for prop in properties:
        prop_explored.append(prop)
        if prop not in config_dict:
            print_red(f'no such property as {'.'.join(prop_explored)}')
            print_red('cannot set compatibility tool')
            return 0
        config_dict = config_dict[prop]

    print_green('Original CompatToolMapping: ' +
                str(config_vdf.data['InstallConfigStore']['Software']['Valve']['Steam']['CompatToolMapping']))

    if app_id in config_dict:
        config_dict.remove_all_for(app_id)

    config_dict[app_id] = VDFDict()
    config_dict[app_id]['name'] = compat_tool
    config_dict[app_id]['config'] = ''
    config_dict[app_id]['priority'] = '250'

    print_green('Modified CompatToolMapping: ' +
                str(config_vdf.data['InstallConfigStore']['Software']['Valve']['Steam']['CompatToolMapping']))

    if not dry_run:
        config_vdf.save()
    else:
        print_yellow('Dry run, not modifying config.vdf')

    return 0


def set_art_work(
        user_id: str,
        app_id: str,
        hero: str | None,
        logo: str | None,
        tenfoot: str | None,
        boxart: str | None,
        icon: str | None,
        dry_run: bool = False,
        ) -> int:
    grid_dir = get_grid_dir(user_id)
    os.makedirs(grid_dir, exist_ok=True)
    success = True
    if hero is not None and not os.path.exists(hero):
        print_red(f'Hero image {hero} does not exist')
        success = False
    if logo is not None and not os.path.exists(logo):
        print_red(f'Logo image {logo} does not exist')
        success = False
    if tenfoot is not None and not os.path.exists(tenfoot):
        print_red(f'Tenfoot image {tenfoot} does not exist')
        success = False
    if boxart is not None and not os.path.exists(boxart):
        print_red(f'Boxart image {boxart} does not exist')
        success = False
    if icon is not None and not os.path.exists(icon):
        print_red(f'Icon {icon} does not exist')
        success = False

    if not success:
        return err.ERROR_ART_NOT_PROPERLY_SET

    copy_artwork('hero', grid_dir, hero, f'{app_id}_hero', dry_run=dry_run)
    copy_artwork('logo', grid_dir, logo, f'{app_id}_logo', dry_run=dry_run)
    copy_artwork('tenfoot', grid_dir, tenfoot, f'{app_id}', dry_run=dry_run)
    copy_artwork('boxart', grid_dir, boxart, f'{app_id}p', dry_run=dry_run)
    copy_artwork('icon', grid_dir, icon, f'{app_id}_icon', dry_run=dry_run)

    return 0


def get_grid_dir(user_id: str) -> str:
    return os.path.expanduser(os.path.join(STEAM_USERDATA_PATH, user_id, 'config', 'grid'))


def copy_artwork(label: str, grid_dir: str, src: str | None, dest_name: str, dry_run: bool = False) -> None:
    if src is None:
        print_yellow(f'No image specified for {label}, skipping...')
        return
    extension = os.path.splitext(src)[1]
    dest = os.path.join(grid_dir, f'{dest_name}{extension}')
    print(f'Copying {src} to {dest}')
    if not dry_run:
        shutil.copy(src, dest)
    else:
        print_yellow(f'Dry run, not actually copying to {dest}')
