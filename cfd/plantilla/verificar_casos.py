"""Verifica que cada caso terminado en cfd/casos este completo: instantes 0..60,
campos clave en cada instante y archivos cerrados con el pie de OpenFOAM.
Compara con la copia de trabajo en WSL si existe. Uso: python3 verificar_casos.py"""
import json
import re
from pathlib import Path

PROY = Path(__file__).resolve().parents[2]
CASOS = PROY / "cfd" / "casos"
ACTIVOS = Path.home() / "desulfuracion" / "activos"
CLAVE = ["alpha.argon", "U.argon", "U.hierro", "p", "p_rgh"]
NUM = re.compile(r"^\d+(\.\d+)?$")


def cerrado(f):
    if not f.is_file() or f.stat().st_size == 0:
        return False
    with open(f, "rb") as h:
        h.seek(max(0, f.stat().st_size - 400))
        return b"// ****" in h.read()


cola = json.loads((PROY / "orquestador" / "cola.json").read_text(encoding="utf-8"))
for c in cola["casos"]:
    d = CASOS / c["id"]
    ts = sorted((float(p.name), p) for p in d.iterdir() if p.is_dir() and NUM.match(p.name)) if d.is_dir() else []
    malos = [p.name for t, p in ts if t > 0 and not all(cerrado(p / k) for k in CLAVE)]
    archivos_d = sum(1 for t, p in ts for f in p.iterdir() if f.is_file())
    w = ACTIVOS / c["id"]
    wts = sorted(float(p.name) for p in w.iterdir() if p.is_dir() and NUM.match(p.name)) if w.is_dir() else []
    ok = ts and ts[-1][0] >= 60 - 1e-6 and not malos and (not wts or len(wts) == len(ts))
    print(f"{c['id']} {c['parametros']['malla']:6s} instantes {len(ts):3d} (WSL {len(wts):3d}) "
          f"final {ts[-1][0] if ts else '-':>9} archivos {archivos_d:5d} "
          f"{'OK' if ok else 'REVISAR'} {('incompletos: ' + ', '.join(malos[:5])) if malos else ''}")
