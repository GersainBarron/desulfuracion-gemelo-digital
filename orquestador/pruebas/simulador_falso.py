#!/usr/bin/env python3
"""Imita a un solver de OpenFOAM para probar el orquestador sin calcular nada.

Lee system/controlDict en cada paso (como runTimeModifiable), arranca desde el
ultimo instante, escribe instantes con el pie de OpenFOAM y obedece stopAt writeNow.
Si existe el archivo FALLAR en el caso, imprime un error fatal y sale.
"""
import re
import sys
import time
from pathlib import Path

caso = Path.cwd()
NUM = re.compile(r"^\d+(\.\d+)?$")
PIE = "\n// ************************************************************************* //\n"


def leer(clave):
    txt = (caso / "system" / "controlDict").read_text()
    return re.search(rf"^\s*{clave}\s+([^;]*);", txt, re.M).group(1).strip()


def escribir(t):
    d = caso / f"{t:g}"
    d.mkdir(exist_ok=True)
    for campo in (caso / "0").iterdir():
        texto = campo.read_text().rsplit("// ****", 1)[0]
        # se escribe en dos partes para que un corte deje un archivo incompleto
        with open(d / campo.name, "w") as f:
            f.write(texto + f"// instante {t:g}\n")
            f.flush()
            time.sleep(0.05)
            f.write(PIE)
    print(f"Time = {t:g}  escrito", flush=True)


previos = [float(p.name) for p in caso.iterdir() if p.is_dir() and NUM.match(p.name)]
t = max(previos) if previos else 0.0
paso = 0.5
print(f"simulador falso: arranca en {t:g}", flush=True)
while True:
    if (caso / "FALLAR").exists():
        print("--> FOAM FATAL ERROR: prueba de divergencia", flush=True)
        sys.exit(1)
    fin = float(leer("endTime"))
    cada = float(leer("writeInterval"))
    if leer("stopAt") == "writeNow":
        escribir(t)
        sys.exit(0)
    time.sleep(0.5)
    t = round(t + paso, 6)
    if abs(t / cada - round(t / cada)) < 1e-9:
        escribir(t)
    if t >= fin - 1e-9:
        if abs(t / cada - round(t / cada)) >= 1e-9:
            escribir(t)
        print("End", flush=True)
        sys.exit(0)
