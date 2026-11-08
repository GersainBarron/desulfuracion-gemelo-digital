#!/usr/bin/env bash
pkill -9 -x pvpython
export HWLOC_COMPONENTS=-gl,-cuda,-nvml,-opencl,-rsmi,-levelzero
cat > /tmp/p.py <<'EOF'
import numpy
print("numpy", numpy.__version__)
from paraview.simple import OpenFOAMReader
print("paraview ok")
EOF
O="$(dirname "$0")/probar_pvpython.log"
timeout -s KILL 120 pvpython --force-offscreen-rendering /tmp/p.py < /dev/null > "$O" 2>&1
echo "codigo=$?" >> "$O"
