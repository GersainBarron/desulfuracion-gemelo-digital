#!/usr/bin/env bash
# Prueba de punta a punta del orquestador con el simulador falso:
# pausa, reanudacion, corte de luz con instante a medio escribir,
# perdida total de WSL (restaurar desde D:) y un caso que diverge.
set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
sed "s#@AQUI@#$AQUI#g" "$AQUI/config.prueba.json" > "$AQUI/config.prueba.local.json"   # rutas de esta carpeta
export ORQ_CONFIG="$AQUI/config.prueba.local.json"
RAIZ="$AQUI/raiz"; ACT=~/desulfuracion/prueba_activos; ORQ="$AQUI/../orquestador.py"
rm -rf "$RAIZ" "$ACT" ~/desulfuracion/orquestador.pid
mkdir -p "$RAIZ/orquestador" "$RAIZ/cfd/plantilla"
cat > "$RAIZ/orquestador/cola.json" <<'EOF'
{"casos": [
 {"id": "c01", "parametros": {"nota": "caso normal"}, "estado": "pendiente"},
 {"id": "c02", "parametros": {"fallar": true}, "estado": "pendiente"}
]}
EOF
estado() { python3 -c "import json;c=json.load(open('$RAIZ/orquestador/cola.json'));print(' '.join(f\"{x['id']}={x['estado']}@{x.get('ultimo_instante')}\" for x in c['casos']))"; }
esperar() { for i in $(seq 1 90); do estado | grep -q "$1" && return 0; sleep 1; done; echo "TIEMPO AGOTADO esperando $1"; return 1; }
arrancar() { python3 "$ORQ" >> "$AQUI/salida_prueba.log" 2>&1 & ORQ_PID=$!; }
: > "$AQUI/salida_prueba.log"

echo "1) arranque y pausa"
arrancar; sleep 5
touch "$RAIZ/orquestador/PAUSA"
esperar "c01=pausado" && echo "   OK pausado: $(estado)"

echo "2) reanudar y corte de luz (kill -9) con instante a medio escribir"
rm "$RAIZ/orquestador/PAUSA"; sleep 3
pkill -9 -f simulador_falso.py; kill -9 $ORQ_PID; sleep 1
ULT=$(ls "$ACT/c01" | grep -E '^[0-9.]+$' | sort -g | tail -1)
NUEVO=$(python3 -c "print(f'{$ULT+0.5:g}')"); mkdir -p "$ACT/c01/$NUEVO"
printf 'FoamFile {}\ninternalField truncado' > "$ACT/c01/$NUEVO/p"
echo "   ultimo bueno $ULT, se planto instante corrupto $NUEVO: $(estado)"
rm -f ~/desulfuracion/orquestador.pid
arrancar; sleep 4
[ -d "$ACT/c01/$NUEVO" ] && echo "   FALLA: no descarto $NUEVO" || echo "   OK descarto el instante corrupto $NUEVO"

echo "3) perdida total de WSL: se borra el caso activo"
kill -9 $ORQ_PID; pkill -9 -f simulador_falso.py; sleep 1
rm -rf "$ACT/c01" ~/desulfuracion/orquestador.pid
arrancar
esperar "c01=terminado" && echo "   OK c01 restaurado desde D: y terminado"
grep -q "restaurado desde respaldo" "$RAIZ/cfd/bitacora/orquestador.log" && echo "   OK la bitacora registra la restauracion"

echo "4) caso que diverge"
esperar "c02=fallido" && echo "   OK c02 marcado fallido tras 2 intentos"
wait $ORQ_PID 2>/dev/null
grep -q "c02 fallo" "$RAIZ/AVISOS.txt" && echo "   OK aviso escrito en AVISOS.txt"
N=$(ls "$RAIZ/cfd/respaldos/c01/t" | wc -l); echo "   respaldos conservados de c01: $N (esperado 2)"
[ -d "$RAIZ/cfd/casos/c01" ] && echo "   OK c01 copiado a cfd/casos"
echo; echo "--- ESTADO.txt final"; cat "$RAIZ/ESTADO.txt"
