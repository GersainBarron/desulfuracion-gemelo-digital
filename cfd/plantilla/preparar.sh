#!/usr/bin/env bash
# Llamado por el orquestador:  preparar.sh <carpeta_caso> <params.json> <nucleos>
source /usr/lib/openfoam/openfoam2606/etc/bashrc >/dev/null 2>&1
set -eo pipefail
python3 "$(dirname "$0")/preparar.py" "$@"
