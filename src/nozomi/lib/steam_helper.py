import hashlib
import os
from nozomi.lib.constants import STEAM_USERDATA_PATH
import contextlib


def find_steam_user_id() -> str | None:
    # steam user id is the name of the directory in the steamapps directory
    # this is the default location for steam library
    userdata_path = os.path.expanduser(STEAM_USERDATA_PATH)
    if not os.path.exists(userdata_path):
        print(f'userdata directory does not exist at {userdata_path}')
        return ''
    steam_user_id = os.listdir(userdata_path)
    if len(steam_user_id) == 0:
        print(f'userdata directory {userdata_path} does not contain any accounts')
        return None
    return steam_user_id[0]


def find_image_by_name(image_name: str, directory: str) -> str | None:
    if not os.path.exists(directory):
        return None

    image_extensions = ['.jpg', '.jpeg', '.png', '.ico']

    for file in os.listdir(directory):
        name, ext = os.path.splitext(file)
        if name == image_name and ext.lower() in image_extensions:
            return os.path.join(directory, file)

    return None


@contextlib.contextmanager
def change_dir(destination):
    prev_dir = os.getcwd()
    os.chdir(destination)
    try:
        yield
    finally:
        os.chdir(prev_dir)


def generate_shortcut_vdf_app_id(seed_str) -> str:
    seed = hashlib.md5(seed_str.encode()).hexdigest()[:8]
    return f'-{int(seed, 16) % 1000000000}'
