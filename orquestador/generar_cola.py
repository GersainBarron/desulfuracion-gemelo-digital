"""Crea o completa cola.json a partir de barrido.json sin tocar casos ya existentes.

Orden: estudio de malla (caso base en gruesa, media y fina) y luego el barrido.
Uso:  python generar_cola.py
"""
import itertools
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
b = json.loads((AQUI / "barrido.json").read_text(encoding="utf-8"))
ruta = AQUI / "cola.json"
cola = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {"casos": []}
existentes = {json.dumps(c["parametros"], sort_keys=True) for c in cola["casos"]}

deseados = []
em = b["estudio_malla"]
for malla in em["mallas"]:
    deseados.append({"factor_caudal_gas": em["factor_caudal_gas"],
                     "profundidad_lanza_m": em["profundidad_lanza_m"], "malla": malla})
for q, h in itertools.product(b["factor_caudal_gas"], b["profundidad_lanza_m"]):
    deseados.append({"factor_caudal_gas": q, "profundidad_lanza_m": h, "malla": b["malla_barrido"]})

n = len(cola["casos"])
for params in deseados:
    clave = json.dumps(params, sort_keys=True)
    if clave in existentes:
        continue
    existentes.add(clave)
    n += 1
    cola["casos"].append({"id": f"c{n:02d}", "parametros": params, "estado": "pendiente"})

ruta.write_text(json.dumps(cola, indent=2, ensure_ascii=False), encoding="utf-8")
for c in cola["casos"]:
    print(c["id"], c["parametros"])
print(f"cola.json: {len(cola['casos'])} casos")
