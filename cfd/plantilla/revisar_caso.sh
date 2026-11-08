#!/usr/bin/env bash
# Resumen fisico de un caso terminado. Uso: revisar_caso.sh <id> [instantes...]
# OpenFOAM no acepta espacios en rutas: se trabaja a traves de ~/desulfuracion/proyecto (enlace).
AQUI="$(cd "$(dirname "$0")" && pwd)"
ENLACE=~/desulfuracion/proyecto
[ -L "$ENLACE" ] || ln -s "$(cd "$AQUI/../.." && pwd)" "$ENLACE"
C="$ENLACE/cfd/casos/$1"; shift
source /usr/lib/openfoam/openfoam2606/etc/bashrc >/dev/null 2>&1
echo "instantes guardados: $(ls "$C" | grep -E '^[0-9.]+$' | wc -l), ultimo: $(ls "$C" | grep -E '^[0-9.]+$' | sort -g | tail -1)"
for x in ${@:-10 30 60}; do
  if [ ! -f "$C/$x/C" ]; then
    (cd "$C" && postProcess -func writeCellCentres -time "$x" > log.centros 2>&1) \
      || { echo "fallo postProcess:"; tail -3 "$C/log.centros"; exit 1; }
  fi
  echo "--- t=$x s"; python3 "$AQUI/revisar_campos.py" "$C" "$x"
done
