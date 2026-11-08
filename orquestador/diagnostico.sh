#!/usr/bin/env bash
# Diagnostico rapido: procesos vivos de la cola y ultimas lineas de cada log.
echo "--- procesos"
ps -eo pid,etime,pcpu,args | grep -E '[o]rquestador.py|[m]pirun|[t]woPhaseEulerFoam' | cut -c1-150 | awk '{print}' | sort -u | head -20
echo "--- c02: final de log.solver"
tail -c 1500 ~/desulfuracion/activos/c02/log.solver
echo; echo "--- instantes de c02 en WSL"
ls ~/desulfuracion/activos/c02/processor0 | grep -E '^[0-9.]+$' | sort -g | tail -3 | tr '\n' ' '
echo; echo "--- uptime de WSL"; uptime -s
