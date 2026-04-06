# nozomi-cli-add_shortcut

## Description

Removes a non-steam game to the steam library via the CLI


```bash
$ ./bin/nozomi-cli remove_shortcut --help
usage: nozomi-cli add_shortcut [-h] --app-name <name> --exe-path <path/to/executable> [--dry-run]

options:
  -h, --help            show this help message and exit
  --app-name <name>     (Required) The name of the shortcut
  --exe-path <path/to/executable>
                        (Required) The full path to the executable
  --dry-run             Performs a dry run
```

Example usage:

```bash
$ ./bin/nozomi-cli remove_shortcut \
  --name "My Game" \
  --path "/path/to/my/game/executable"
```

## Notes:
- This command will remove the shortcut from steam
- AppId internally in steam is a signed integer, where it may be that positive numbers are official steam games and negative are reserved for non-steam games
(*citation needed here, I have not found any official documentation on this)
- You can run this while steam is open, however you will need to restart steam upon completion for the changes to take effect
