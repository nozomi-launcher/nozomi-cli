# nozomi-cli-install

## Description

Installs a non-steam game using nozomi-cli manifest files

```bash
$ ./bin/nozomi-cli install --help        
usage: __main__.py install [-h] [--directory <directory>] [--dry-run]

options:
  -h, --help            show this help message and exit
  --directory <directory>
                        The directory to install the game from
  --dry-run             Do not actually modify steam
```

Example usage:

```bash
$ ./bin/nozomi-cli install --directory /path/to/game
```

## Notes:
- This command will install the game to steam
- The directory must contain a `.nozomi` directory with a `manifest.json` file
- Artwork is optional, and can be placed in the `.nozomi/steamgrid` directory
  - The icon must be named `icon`
    - The icon must be a `.ico` file preferably, but `.png` and `.jpg`/`.jpeg` is also supported
  - The hero image must be named `hero`
  - The logo image must be named `logo`
  - The boxart image must be named `boxart`
  - The tenfoot image must be named `tenfoot`
  All images must be `.png` files preferably, but `.jpg`/`.jpeg` is also supported