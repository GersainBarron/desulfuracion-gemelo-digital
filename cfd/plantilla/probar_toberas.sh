#!/usr/bin/env bash
# Prueba del caso con toberas: malla fina, 8 procesos, 2 s simulados. Mide el ritmo.
source /usr/lib/openfoam/openfoam2606/etc/bashrc >/dev/null 2>&1
export HWLOC_COMPONENTS=-gl,-cuda,-nvml,-opencl,-rsmi,-levelzero
D=~/desulfuracion/prueba_toberas; rm -rf "$D"; mkdir -p "$D"
O="$(dirname "$0")/probar_toberas.log"; : > "$O"
echo '{"factor_caudal_gas": 1.0, "profundidad_lanza_m": 2.0, "malla": "fina", "toberas": true}' > "$D/p.json"
bash "$(dirname "$0")/preparar.sh" "$D/c" "$D/p.json" 8 >> "$O" 2>&1 || { echo "FALLO preparar" >> "$O"; tail -20 "$D/c/log."* >> "$O" 2>/dev/null; exit 1; }
grep -A3 -E '^\s*(inlet|punta)' "$D/c/constant/polyMesh/boundary" >> "$O"
grep -A6 'inlet' "$D/c/0/U.argon" | head -8 >> "$O"
grep -c 'walls|punta' "$D/c/0/U.hierro" >> "$O"
cd "$D/c"
sed -i 's/^endTime .*/endTime         2;/' system/controlDict
SECONDS=0
timeout 3600 mpirun --use-hwthread-cpus -np 8 twoPhaseEulerFoam -parallel < /dev/null > log.solver 2>&1
echo "solver codigo=$? segundos_reales=$SECONDS" >> "$O"
grep -m1 -A6 FATAL log.solver >> "$O"
grep '^Time = ' log.solver | tail -1 >> "$O"
grep '^deltaT' log.solver | tail -1 >> "$O"
grep 'Courant Number mean' log.solver | tail -1 >> "$O"
echo FIN >> "$O"
