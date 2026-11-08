#!/usr/bin/env bash
# Extrae todos los casos terminados que aun no tengan extraccion/<caso>/COMPLETO.
# Reanudable: si se corta, al relanzarlo sigue con los que falten.
# Uso: extraer_todo.sh [caso ...]      (sin argumentos: todos)
export HWLOC_COMPONENTS=-gl,-cuda,-nvml,-opencl,-rsmi,-levelzero
AQUI="$(cd "$(dirname "$0")" && pwd)"
ENLACE=~/desulfuracion/proyecto          # OpenFOAM/ParaView y las rutas con espacios
[ -L "$ENLACE" ] || ln -s "$(cd "$AQUI/.." && pwd)" "$ENLACE"
LOG="$AQUI/extraccion.log"
casos="${*:-$(ls "$ENLACE/cfd/casos")}"
for c in $casos; do
  [ -f "$AQUI/$c/COMPLETO" ] && { echo "$c: ya extraido" >> "$LOG"; continue; }
  params=$(python3 -c "import json;print(json.dumps(next(x['parametros'] for x in json.load(open('$ENLACE/orquestador/cola.json'))['casos'] if x['id']=='$c')))")
  echo "[$(date '+%F %T')] $c: inicia" >> "$LOG"
  pvpython --force-offscreen-rendering "$AQUI/extraer.py" "$ENLACE/cfd/casos/$c" "$ENLACE/extraccion/$c" "$params" \
    < /dev/null >> "$LOG" 2>&1 || echo "[$(date '+%F %T')] $c: FALLO (ver arriba)" >> "$LOG"
done
echo "[$(date '+%F %T')] extraccion terminada" >> "$LOG"
