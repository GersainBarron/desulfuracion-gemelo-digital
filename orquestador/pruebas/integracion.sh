#!/usr/bin/env bash
# Prueba de tiempos e integracion con OpenFOAM real: malla media, 8 nucleos,
# 3 s simulados con una pausa y reanudacion a la mitad.
AQUI="$(cd "$(dirname "$0")" && pwd)"
sed "s#@AQUI@#$AQUI#g" "$AQUI/config.integracion.json" > "$AQUI/config.integracion.local.json"   # rutas de esta carpeta
export ORQ_CONFIG="$AQUI/config.integracion.local.json"
RAIZ="$AQUI/raiz_of"; ACT=~/desulfuracion/prueba_of_activos
rm -rf "$RAIZ" "$ACT"; mkdir -p "$RAIZ/orquestador" "$RAIZ/cfd/plantilla"
echo '{"casos": [{"id": "t01", "parametros": {"factor_caudal_gas": 1.0, "profundidad_lanza_m": 2.0, "malla": "media"}, "estado": "pendiente"}]}' > "$RAIZ/orquestador/cola.json"
SECONDS=0
python3 "$AQUI/../orquestador.py" > "$AQUI/salida_integracion.log" 2>&1 &
PID=$!
# pausa cuando exista el primer instante respaldado
for i in $(seq 1 600); do [ -d "$RAIZ/cfd/respaldos/t01/t/1" ] && break; sleep 2; done
echo "primer segundo simulado listo a los $SECONDS s reales"
touch "$RAIZ/orquestador/PAUSA"
for i in $(seq 1 300); do grep -q '"estado": "pausado"' "$RAIZ/orquestador/cola.json" && break; sleep 2; done
echo "en pausa a los $SECONDS s: $(grep -o '"ultimo_instante": "[^"]*"' "$RAIZ/orquestador/cola.json")"
sleep 10; rm "$RAIZ/orquestador/PAUSA"
wait $PID
echo "termino a los $SECONDS s reales"
grep -E "t01:" "$RAIZ/cfd/bitacora/orquestador.log"
cat "$RAIZ/../raiz_of/cfd/casos/t01/resumen_caso.json" 2>/dev/null | head -4
ls "$RAIZ/cfd/casos/t01" | tr '\n' ' '
