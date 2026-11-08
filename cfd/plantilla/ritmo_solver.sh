#!/usr/bin/env bash
# Por que cambia el ritmo: paso de tiempo, Courant y segundos reales por paso del caso activo.
L=~/desulfuracion/activos/${1:-c02}/log.solver
echo "paso de tiempo (deltaT) en distintos momentos:"
grep '^deltaT' "$L" | awk 'NR%2000==1' | tail -6
echo "ultimos:"; grep '^deltaT' "$L" | tail -1; grep 'Courant Number mean' "$L" | tail -1
grep 'ExecutionTime' "$L" | tail -1
grep -c '^Time = ' "$L" | xargs echo "pasos totales en este tramo:"
