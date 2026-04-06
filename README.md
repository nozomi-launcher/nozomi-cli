# Nozomi CLI

## Description

All in one solution for managing all games within steam.

## Development

### Requirements
- [Python 3.10+](https://www.python.org/downloads/)
- [PyCharm (optional, recommended)](https://www.jetbrains.com/pycharm/download/)

### Getting started

Recommended to use virtual environments to avoid conflicts with system packages.

```bash
$ cd /path/to/nozomi/project/root
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install -e .
$ python3 ./src/nozomi/cli --help
```

## How to build nozomi-cli

Currently, the project uses pyinstaller to build the binary. This is subject to change.

```bash
$ cd /path/to/nozomi/project/root
$ ./scripts/build.sh
$ ./bin/nozomi-cli --help
```

To clean up all build artifacts, run:

```bash
$ ./scripts/clean.sh
```

## how to use nozomi-cli
    
```bash
$ ./bin/nozomi-cli --help
usage: nozomi-cli [-h] [--version] [command] ...

All in one steam game manager

positional arguments:
  [command]        Available commands
    info           prints information about the current steam installation
    add_shortcut   adds an executable shortcut to steam
    remove_shortcut
                   removes an executable shortcut to steam
    install        installs a non-steam game

options:
  -h, --help    show this help message and exit
  --version     Print the version of nozomi
```

### Commands

- [info](src/nozomi/cli/commands/info/README.md)
- [add_shortcut](src/nozomi/cli/commands/add_shortcut/README.md)
- [remove_shortcut](src/nozomi/cli/commands/remove_shortcut/README.md)
- [install](src/nozomi/cli/commands/install/README.md)
