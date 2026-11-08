#!/usr/bin/env bash
# Detiene solo el proceso del orquestador (usar con la cola en pausa: no toca OpenFOAM).
for p in $(pgrep -f '[o]rquestador/orquestador.py'); do kill "$p"; echo "detenido orquestador $p"; done
