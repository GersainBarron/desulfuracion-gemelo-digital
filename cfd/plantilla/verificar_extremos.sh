#!/usr/bin/env bash
# Verifica que la plantilla prepare los casos extremos de la cola (solo malla, sin calcular)
source /usr/lib/openfoam/openfoam2606/etc/bashrc
D=~/desulfuracion/prueba_extremos; rm -rf "$D"; mkdir -p "$D"
for combo in "2.0 2.5 media" "0.5 1.5 media" "1.0 2.0 fina"; do
  set -- $combo
  echo "{\"factor_caudal_gas\": $1, \"profundidad_lanza_m\": $2, \"malla\": \"$3\"}" > "$D/p.json"
  if bash "$(dirname "$0")/preparar.sh" "$D/c" "$D/p.json" 8 > "$D/log" 2>&1; then
    python3 -c "import json;r=json.load(open('$D/c/resumen_caso.json'));print('$combo', '->', r['celdas'], 'celdas, malla_ok', r['malla_ok'], ', punta y =', r['punta_lanza_y_m'])"
  else
    echo "$combo -> FALLO"; tail -5 "$D/log"
  fi
done
rm -rf "$D"
