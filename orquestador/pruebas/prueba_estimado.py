"""Prueba del termino estimado con la cola real (solo lee; no toca el orquestador en marcha)."""
import json
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
os.environ["ORQ_CONFIG"] = str(AQUI / "config.prueba.json")
sys.path.insert(0, str(AQUI.parent))
import orquestador as o  # noqa: E402

cola = json.loads((AQUI.parent / "cola.json").read_text(encoding="utf-8"))
actual = next(c for c in cola["casos"] if c["estado"] == "corriendo")
o.CFG["endTime"] = 60
sim, ritmo = 11.0, 32.1 / 3600            # lo que mostraba ESTADO.txt
h = o.estimar_horas_restantes(cola, actual, sim, ritmo)
print(f"caso actual {actual['id']}; faltan ~{h:.1f} h en total")
for c in cola["casos"]:
    print(c["id"], c["estado"], c["parametros"].get("malla"), c.get("duracion_h"))
