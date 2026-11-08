"""Prepara los datos y medios que usa la pagina (todo local, sin red).
Uso: python web/construir_datos.py
Escribe web/datos/*.json, web/medios/* y copia three.js a web/vendor."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

WEB = Path(__file__).resolve().parent
RAIZ = WEB.parent
DATOS = WEB / "datos"
MEDIOS = WEB / "medios"
import os
# three.js r1xx (MIT): carpeta con three.module.js y addons/; por omision la copia que ya trae web/vendor
VENDOR_LAB = Path(os.environ.get("THREEJS_VENDOR", str(WEB / "vendor")))
DATOS.mkdir(exist_ok=True)
MEDIOS.mkdir(exist_ok=True)

# 1. Resumen del barrido (incluye c12) ------------------------------------------
subprocess.run([sys.executable, str(RAIZ / "extraccion" / "resumen_barrido.py")], check=True)
shutil.copy2(RAIZ / "extraccion" / "resumen_barrido.json", DATOS / "barrido.json")

# 2. Parametros y validacion del modelo -------------------------------------------
shutil.copy2(RAIZ / "modelo" / "parametros.json", DATOS / "parametros.json")

# 3. Lineas de corriente 3D del caso c12, aligeradas -------------------------------
fuente = json.loads((RAIZ / "extraccion" / "c12" / "lineas3d.json").read_text(encoding="utf-8"))
salida, puntos = [], 0
for ln in fuente["lineas"]:
    p, v = ln["p"], ln["v"]
    if len(p) < 8:
        continue
    idx = list(range(0, len(p), 3))
    if idx[-1] != len(p) - 1:
        idx.append(len(p) - 1)
    salida.append({"p": [round(c, 3) for i in idx for c in p[i]],
                   "v": [round(float(v[i]), 4) for i in idx]})
    puntos += len(idx)
meta = json.loads((RAIZ / "extraccion" / "c12" / "meta.json").read_text(encoding="utf-8"))
(DATOS / "lineas_c12.json").write_text(json.dumps({"geometria": meta["geometria"], "lineas": salida},
                                                  separators=(",", ":")), encoding="utf-8")
print(f"lineas: {len(salida)}  puntos: {puntos}")

# 4. Video y poster -----------------------------------------------------------------
shutil.copy2(RAIZ / "blender" / "render" / "c12.mp4", MEDIOS / "c12.mp4")
cuadros = sorted((RAIZ / "blender" / "render" / "c12").glob("rotulado_*.png"))
poster = cuadros[min(200, len(cuadros) - 1)]
Image.open(poster).convert("RGB").save(MEDIOS / "c12_poster.jpg", quality=88)
control = RAIZ / "extraccion" / "c12" / "control_lineas.png"
if control.exists():
    Image.open(control).convert("RGB").save(MEDIOS / "c12_lineas.jpg", quality=85)

# 5. three.js local -----------------------------------------------------------------
for rel in ["three.module.js", "addons/controls/OrbitControls.js"]:
    destino = WEB / "vendor" / rel
    if (VENDOR_LAB / rel).resolve() == destino.resolve():
        continue
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(VENDOR_LAB / rel, destino)
print("listo")
