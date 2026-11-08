#!/usr/bin/env bash
# Extrae todos los casos y luego calcula sus lineas de corriente y vistas de control
# (con el Python de Windows del laboratorio). Reanudable.
AQUI="$(cd "$(dirname "$0")" && pwd)"
pgrep -f '[e]xtraer_todo.sh' > /dev/null && exit 0
bash "$AQUI/extraer_todo.sh"
PY="${DESULF_PYTHON:-python3}"   # Python con numpy, matplotlib y Pillow
for c in $(ls "$AQUI"); do
  [ -f "$AQUI/$c/COMPLETO" ] || continue
  [ -f "$AQUI/$c/lineas3d.json" ] && [ -f "$AQUI/$c/control.png" ] && continue
  echo "[$(date '+%F %T')] $c: lineas y vistas" >> "$AQUI/extraccion.log"
  (cd "$AQUI" && "$PY" lineas.py "$c" && "$PY" vista_control.py "$c" && "$PY" vista_lineas.py "$c") >> "$AQUI/extraccion.log" 2>&1
done
echo "[$(date '+%F %T')] todo listo" >> "$AQUI/extraccion.log"
