#!/usr/bin/env bash
L=~/desulfuracion/prueba_toberas/c/log.solver
grep -m1 -A6 FATAL "$L"
grep '^Time = ' "$L" | tail -1
grep '^deltaT' "$L" | tail -1
grep 'Courant Number mean' "$L" | tail -1
grep 'ExecutionTime' "$L" | tail -1
tail -2 "$(dirname "$0")/probar_toberas.log"
