#!/usr/bin/env bash
# Lanza extraer_todo.sh desacoplado (sigue aunque se cierre esta ventana).
AQUI="$(cd "$(dirname "$0")" && pwd)"
pgrep -f '[e]xtraer_todo.sh' > /dev/null && { echo "ya esta corriendo"; exit 0; }
setsid nohup bash "$AQUI/extraer_todo.sh" "$@" > /dev/null 2>&1 < /dev/null &
echo "extraccion lanzada; progreso en extraccion/extraccion.log"
