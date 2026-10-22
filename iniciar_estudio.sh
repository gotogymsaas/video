#!/usr/bin/env sh
set -eu
studio_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$studio_root"
exec python3 iniciar_estudio.py
