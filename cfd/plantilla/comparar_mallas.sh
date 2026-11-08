#!/usr/bin/env bash
# Estudio de malla del caso base: c01 gruesa, c02 media, c03 fina, en el ultimo instante de cada uno
# (tras reanudar, el final puede quedar en 60.13 s y no en 60 s exactos).
AQUI="$(cd "$(dirname "$0")" && pwd)"
CASOS="$AQUI/../casos"
for c in c01 c02 c03; do
  ult=$(ls "$CASOS/$c" | grep -E '^[0-9.]+$' | sort -g | tail -1)
  echo "===== $c (t = $ult s)"
  bash "$AQUI/revisar_caso.sh" "$c" "$ult" | tail -3
done
