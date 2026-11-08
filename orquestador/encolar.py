"""Agrega un caso a cola.json de forma atomica (seguro con el orquestador en espera).
Uso: python encolar.py '{"factor_caudal_gas": 1.0, "profundidad_lanza_m": 2.0, "malla": "fina", "toberas": true}'"""
import json
import os
import sys
from pathlib import Path

ruta = Path(__file__).resolve().parent / "cola.json"
params = json.loads(sys.argv[1])
cola = json.loads(ruta.read_text(encoding="utf-8"))
if any(c["parametros"] == params for c in cola["casos"]):
    sys.exit("ya existe un caso con esos parametros")
if any(c["estado"] == "corriendo" for c in cola["casos"]):
    sys.exit("hay un caso corriendo: pausa la cola antes de editarla")
cid = f"c{len(cola['casos']) + 1:02d}"
cola["casos"].append({"id": cid, "parametros": params, "estado": "pendiente"})
tmp = ruta.with_suffix(".tmp")
tmp.write_text(json.dumps(cola, indent=2, ensure_ascii=False), encoding="utf-8")
os.replace(tmp, ruta)
print(f"{cid} encolado: {params}")
