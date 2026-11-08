#!/usr/bin/env bash
# Prepara un caso de juguete con la misma estructura que uno de OpenFOAM.
# Uso: preparar_falso.sh <carpeta_caso> <params.json> <nucleos>
set -euo pipefail
caso="$1"
mkdir -p "$caso/system" "$caso/0" "$caso/constant"
pie='// ************************************************************************* //'
cat > "$caso/system/controlDict" <<EOF
FoamFile { format ascii; class dictionary; object controlDict; }
application     simuladorFalso;
startFrom       latestTime;
stopAt          endTime;
endTime         10;
writeControl    adjustableRunTime;
writeInterval   2;
maxCo           0.5;
runTimeModifiable yes;
$pie
EOF
for campo in alpha.argon U.argon U.hierro p p_rgh; do
  printf 'FoamFile { object %s; }\ninternalField uniform 0;\n%s\n' "$campo" "$pie" > "$caso/0/$campo"
done
echo "placeholder de malla" > "$caso/constant/malla.txt"
if grep -q '"fallar": true' "$2"; then touch "$caso/FALLAR"; fi
echo '{"caso": "prueba", "celdas": 0}' > "$caso/resumen_caso.json"   # el orquestador lo exige al terminar de preparar
echo "caso de prueba listo en $caso"
