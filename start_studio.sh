#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo 'Instala Python 3.11 o superior.'; exit 1; }
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || { echo 'Instala FFmpeg y FFprobe y añádelos a PATH. Consulta docs/PRODUCCION.md.'; exit 1; }
if [ ! -f .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install .
.venv/bin/python -m qaf_video doctor
.venv/bin/python -m qaf_video serve --workspace projects
