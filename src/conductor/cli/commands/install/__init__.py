import json
import shutil
import subprocess
import jsonschema.exceptions
import os
import tempfile
import conductor.cli.commands.install.error_codes as err
from argparse import Namespace
from conductor.lib.command import BaseCommand
from jsonschema import validate, FormatChecker
from conductor.cli.console_colors import *
from urllib.parse import urlparse
from conductor.lib.steam_helper import find_image_by_name, change_dir
from conductor.cli.commands.add_shortcut import add_non_steam_game


class Command(BaseCommand):
    def __init__(self):
        self.__command_name = 'install'

    def get_command_str(self) -> str:
        return self.__command_name

    def register_options(self, subparsers) -> None:
        install_command = subparsers.add_parser(self.__command_name, help='installs a non-steam game')
        install_command.add_argument(
            '--directory',
            metavar='<directory>',
            help='The directory to install the game from'
        )
        install_command.add_argument(
            '--dry-run',
            action='store_true',
            help='Do not actually modify steam'
        )

    def command(self, args: Namespace) -> int:
        if "dry_run" in args and args.dry_run is True:
            print_yellow('dry run, not installing anything')

        programs_to_check = ['rsync', 'wget']
        program_missing = False
        for program in programs_to_check:
            if not self.verify_programs_installed(program):
                print_red(f'{program} is not installed')
                program_missing = True
        if program_missing:
            return err.PROGRAM_NOT_INSTALLED

        expanded_directory = os.path.expanduser(args.directory)
        conductor_directory = f'{expanded_directory}/.conductor'
        if not os.path.exists(conductor_directory):
            print_red(f'directory {expanded_directory} is not installable by conductor')
            return err.NOT_A_CONDUCTOR_DIRECTORY

        manifest = self.load_manifest(expanded_directory)

        if manifest is None:
            return err.MANIFEST_LOAD_ERROR

        result = self.execute_install_scripts(
            manifest=manifest,
            directory=f'{conductor_directory}/scripts',
            dry_run=args.dry_run,
            post_install=False,
            pre_install=True)
        if result != 0:
            return result

        result = self.install(manifest, expanded_directory, args.dry_run)
        if result != 0:
            return result

        if not add_non_steam_game(
            app_name=manifest['steam']['appName'],
            exe_path=manifest['steam']['exePath'],
            compat_tool=manifest['steam']['compatTool'] if 'compatTool' in manifest['steam'] else None,
            hero=find_image_by_name('hero', f'{conductor_directory}/steamgrid'),
            logo=find_image_by_name('logo', f'{conductor_directory}/steamgrid'),
            tenfoot=find_image_by_name('tenfoot', f'{conductor_directory}/steamgrid'),
            boxart=find_image_by_name('boxart', f'{conductor_directory}/steamgrid'),
            icon=find_image_by_name('icon', f'{conductor_directory}/steamgrid'),
            launch_options=manifest['steam']['launchOptions'] if 'launchOptions' in manifest['steam'] else None,
            dry_run=args.dry_run,
        ) == 0:
            return err.ERROR_ADDING_SHORTCUT

        return self.execute_install_scripts(
            manifest=manifest,
            directory=f'{conductor_directory}/scripts',
            dry_run=args.dry_run,
            post_install=True,
            pre_install=False)

    schema = {
        'type': 'object',
        'properties': {
            'install': {
                'type': 'object',
                'properties': {
                    'files': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'source': {
                                    'type': 'string',
                                    'format': 'uri'
                                },
                                'destination': {
                                    'type': 'string',
                                    'format': 'filesystem-path'
                                }
                            },
                            'required': ['source', 'destination']
                        },
                        'minItems': 1
                    }
                }
            },
            'steam': {
                'type': 'object',
                'properties': {
                    'appName': {
                        'type': 'string'
                    },
                    'exePath': {
                        'type': 'string',
                        'format': 'filesystem-path'
                    },
                    'compatTool': {
                        'type': 'string'
                    },
                    'launchOptions': {
                        'type': 'string'
                    }
                },
                'required': ['appName', 'exePath']
            },
            'pre-install': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'format': 'file-exists'
                }
            },
            'post-install': {
                'type': 'array',
                'items': {
                    'type': 'string',
                    'format': 'file-exists'
                }
            }
        }
    }

    @staticmethod
    def is_valid_filesystem_path(instance):
        return os.path.isabs(os.path.expanduser(instance))

    @staticmethod
    def is_valid_uri(instance):
        return (urlparse(instance).scheme in ['file'] and
                os.path.exists(urlparse(instance).netloc + urlparse(instance).path))

    @staticmethod
    def file_exists(instance):
        return os.path.exists(f'.conductor/scripts/{instance}')

    format_checker = FormatChecker()
    format_checker.checks('filesystem-path')(is_valid_filesystem_path)
    format_checker.checks('file-exists')(file_exists)
    format_checker.checks('uri')(is_valid_uri)

    def load_manifest(self, directory: str) -> None | dict:
        with change_dir(directory):
            if not os.path.exists(f'.conductor/manifest.json'):
                print_red('Manifest file does not exist')
                return None
            with open(f'.conductor/manifest.json') as file:
                file_contents = file.read()
                manifest_contents = json.loads(file_contents)

            try:
                validate(instance=manifest_contents, schema=self.schema, format_checker=self.format_checker)
                print('Manifest is valid')
            except jsonschema.exceptions.ValidationError as validation_error:
                print_red(f'Manifest is invalid: {validation_error.message}')
                raise

        return manifest_contents

    @staticmethod
    def verify_programs_installed(program_name):
        return shutil.which(program_name) is not None

    @staticmethod
    def install(manifest: dict, directory: str, dry_run: bool) -> int:
        with change_dir(directory):
            try:
                install_files = manifest['install']['files']
                for file in install_files:
                    source = file['source']
                    destination = os.path.expanduser(file['destination'])
                    if not dry_run:
                        p = urlparse(source)
                        if p.scheme == 'file':
                            source_target = p.netloc + p.path
                        else:
                            raise Exception(f'Unsupported source type {p.scheme}')
                        rsync_command = [
                            'rsync',
                            '-a',
                            '--progress',
                            '--delete',
                            '--delete-delay',
                            '--prune-empty-dirs',
                            source_target,
                            destination
                        ]
                        subprocess.run(rsync_command, check=True)
                    print_green(f'Copied {source} to {destination}')
                return 0
            except Exception as e:
                print_red(f'Error installing files: {e}')
                return err.ERROR_INSTALLING_FILES

    @staticmethod
    def execute_install_scripts(
            manifest: dict,
            directory: str,
            dry_run: bool,
            post_install: bool,
            pre_install: bool) -> int:
        if post_install == pre_install:
            print_yellow("pre_install and post_install cannot be the same value")
            return 0
        protocol = 'post-install' if post_install else 'pre-install'
        if protocol in manifest:
            for script in manifest[protocol]:
                script_to_execute = os.path.join(directory, script)
                if not os.path.exists(script_to_execute):
                    print_red(f'Script {script_to_execute} does not exist')
                    return err.INSTALL_SCRIPT_NOT_FOUND
                if not os.access(script_to_execute, os.X_OK):
                    print_red(f'Script {script_to_execute} is not executable')
                    return err.INSTALL_SCRIPT_NOT_EXECUTABLE
                if dry_run:
                    print_yellow(f'Dry run, did not execute {protocol} script {script_to_execute}')
                    continue

                temp_script_path = None
                try:
                    fd, temp_script_path = tempfile.mkstemp(suffix='.sh', dir='/tmp', text=True)
                    os.close(fd)
                    shutil.copy2(script_to_execute, temp_script_path)
                    os.chmod(temp_script_path, 0o755)
                    subprocess.run([temp_script_path], check=True)
                    print_green(f'Executed {protocol} script {script_to_execute}')
                except subprocess.CalledProcessError as e:
                    print_red(f'Error executing {protocol} script {script_to_execute}: {e}')
                    return err.ERROR_EXECUTING_INSTALL_SCRIPT
                except Exception as e:
                    print_red(f'Error preparing {protocol} script {script_to_execute}: {e}')
                    return err.ERROR_EXECUTING_INSTALL_SCRIPT
                finally:
                    if temp_script_path and os.path.exists(temp_script_path):
                        os.remove(temp_script_path)
        return 0
