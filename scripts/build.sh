#!/usr/bin/env bash

set -euo pipefail

pip3 install -e .
pyinstaller --onefile --clean --name nozomi-cli src/nozomi/cli/__main__.py --dist bin
