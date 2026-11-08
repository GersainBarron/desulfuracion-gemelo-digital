"""Resumen fisico de un instante, separando el bano de la zona de superficie libre.
Uso: python3 revisar_campos.py <carpeta_caso> <instante>
Requiere <instante>/C (centros de celda): se genera con  postProcess -func writeCellCentres -time <t>"""
import json
import math
import re
import sys
from pathlib import Path

caso, t = Path(sys.argv[1]), sys.argv[2]


def interno(campo):
    txt = (caso / t / campo).read_text()
    m = re.search(r"internalField\s+nonuniform\s+List<\w+>\s*\n?(\d+)\s*\n?\(", txt)
    if not m:
        return None
    cuerpo = txt[m.end():txt.index("\n)", m.end())]
    if "(" in cuerpo:
        return [tuple(map(float, v.split())) for v in re.findall(r"\(([^()]*)\)", cuerpo)]
    return [float(x) for x in cuerpo.split()]


H = json.loads((caso / "resumen_caso.json").read_text())["altura_bano_m"]
a, u, ug, c = (interno(f) for f in ("alpha.argon", "U.hierro", "U.argon", "C"))
bano = [i for i, (x, y, z) in enumerate(c) if y < H - 0.2]          # lejos de la superficie
sup = [i for i, (x, y, z) in enumerate(c) if H - 0.2 <= y <= H + 0.2]
mag = [math.sqrt(sum(v * v for v in u[i])) for i in range(len(u))]
pluma = [i for i in bano if a[i] > 0.001]


def resumen(idx):
    m = sorted(mag[i] for i in idx)
    return f"media {sum(m)/len(m):.3g} m/s, p95 {m[int(0.95*len(m))]:.3g} m/s, max {m[-1]:.3g} m/s"


print(f"bano (y < {H-0.2:.2f} m, {len(bano)} celdas): arrabio {resumen(bano)}")
print(f"franja de superficie (+-0.2 m): arrabio {resumen(sup)}")
print(f"pluma en el bano (gas > 0.1%): {len(pluma)} celdas, "
      f"gas max {max(a[i] for i in pluma):.3g}, argon sube hasta {max(ug[i][1] for i in pluma):.3g} m/s")
