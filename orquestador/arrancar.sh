#!/usr/bin/env bash
# Arranca el orquestador desacoplado de la consola (setsid + nohup, salida a archivo)
# y mantiene abierta esta sesion de WSL mientras el orquestador siga vivo.
# Lo llaman la tarea programada y Reanudar.bat; si ya corre, solo hace de guardia.
AQUI="$(cd "$(dirname "$0")" && pwd)"
SALIDA="$AQUI/../cfd/bitacora/orquestador.salida.log"
mkdir -p "$(dirname "$SALIDA")"
if ! pgrep -f '[o]rquestador/orquestador.py' > /dev/null; then
  setsid nohup python3 "$AQUI/orquestador.py" >> "$SALIDA" 2>&1 < /dev/null &
  sleep 5
fi
while pgrep -f '[o]rquestador/orquestador.py' > /dev/null; do sleep 60; done
