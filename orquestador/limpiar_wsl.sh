#!/usr/bin/env bash
# Borra la copia de trabajo en WSL solo de los casos cuya copia en D: esta verificada.
set -u
PROY="$(cd "$(dirname "$0")/.." && pwd)"
salida=$(python3 "$PROY/cfd/plantilla/verificar_casos.py")
echo "$salida"
if echo "$salida" | grep -q REVISAR; then echo "Hay casos por revisar: no se borra nada."; exit 1; fi
df -h ~ | tail -1
for c in $(echo "$salida" | awk '$NF=="OK"{print $1}'); do rm -rf ~/desulfuracion/activos/"$c" ~/desulfuracion/activos/"$c".*; done
rm -rf ~/desulfuracion/prueba_activos ~/desulfuracion/prueba_of_activos ~/desulfuracion/prueba_malla ~/desulfuracion/prueba_extremos
du -sh ~/desulfuracion; df -h ~ | tail -1
