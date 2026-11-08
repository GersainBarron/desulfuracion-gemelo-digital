"""Lineas de corriente del arrabio a partir del flujo promedio (promedio.npz).

Uso: python lineas.py c01 [c02 ...]
Salida en extraccion/<caso>/:
  lineas3d.json     polilineas 3D del flujo promedio (para Blender y three.js)
  lineas_corte.json polilineas 2D en el corte z = 0 (para animar sobre el corte)
Cada linea: {"p": [[x, y, z], ...], "v": [velocidad en cada punto, m/s]}.
Integracion RK4 con interpolacion trilineal, en ambos sentidos desde semillas al azar
(semilla fija: el resultado es reproducible). Solo dentro del liquido (gas < 0.5).
"""
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RNG = np.random.default_rng(2015)


class Campo:
    """Campo vectorial en una malla regular con interpolacion lineal (2D o 3D)."""

    def __init__(self, u, valido, lo, hi):
        self.u, self.valido = u, valido
        self.lo, self.hi = np.array(lo, float), np.array(hi, float)
        self.n = np.array(valido.shape[::-1])                   # (nx, ny[, nz])
        self.h = (self.hi - self.lo) / (self.n - 1)

    def __call__(self, p):
        f = (p - self.lo) / self.h
        if np.any(f < 0) or np.any(f > self.n - 1):
            return None
        i = np.minimum(f.astype(int), self.n - 2)
        w = f - i
        acc, ok = 0.0, 1.0
        for esquina in np.ndindex(*(2,) * len(p)):
            e = np.array(esquina)
            peso = np.prod(np.where(e, w, 1 - w))
            idx = tuple((i + e)[::-1])                          # arreglos en orden [z,] y, x
            acc = acc + peso * self.u[idx]
            ok = ok * (1.0 if self.valido[idx] or peso < 1e-9 else 0.0)
        return acc if ok else None


def trazar(campo, semilla, paso, max_pasos=500):
    def mitad(signo):
        pts, vel = [], []
        p = semilla.copy()
        for _ in range(max_pasos):
            k1 = campo(p)
            if k1 is None:
                break
            s = np.linalg.norm(k1)
            if s < 1e-4:
                break
            pts.append(p.copy()); vel.append(s)
            def dir_(q):
                v = campo(q)
                return None if v is None else signo * v / max(np.linalg.norm(v), 1e-9)
            a = signo * k1 / s
            b = dir_(p + 0.5 * paso * a)
            if b is None: break
            c = dir_(p + 0.5 * paso * b)
            if c is None: break
            d = dir_(p + paso * c)
            if d is None: break
            p = p + paso / 6 * (a + 2 * b + 2 * c + d)
        return pts, vel
    atras, va = mitad(-1)
    adelante, vd = mitad(+1)
    pts = atras[::-1][:-1] + adelante if atras else adelante
    vel = va[::-1][:-1] + vd if va else vd
    return pts, vel


def exportar(lineas, ruta, decimales=3):
    out = [{"p": np.round(np.array(p), decimales).tolist(), "v": np.round(np.array(v), 4).tolist()}
           for p, v in lineas]
    ruta.write_text(json.dumps({"lineas": out}, separators=(",", ":")))
    return len(out), sum(len(l["p"]) for l in out)


for cid in sys.argv[1:]:
    d = AQUI / cid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    pr = np.load(d / "promedio.npz")
    # ---- 3D ----
    b = meta["volumen"]["bounds"]
    liq3 = (pr["vol_mascara"] > 0) & (pr["vol_alpha"].astype(float) < 0.5)
    campo3 = Campo(pr["vol_u"].astype(float), liq3, b[0::2], b[1::2])
    zz, yy, xx = np.nonzero(liq3)
    elegidos = RNG.choice(len(xx), size=min(400, len(xx)), replace=False)
    lineas3 = []
    for k in elegidos:
        s = campo3.lo + np.array([xx[k], yy[k], zz[k]]) * campo3.h + RNG.uniform(-0.4, 0.4, 3) * campo3.h
        pts, vel = trazar(campo3, s, paso=0.03)
        if len(pts) >= 15:
            lineas3.append((pts, vel))
    n3 = exportar(lineas3, d / "lineas3d.json")
    # ---- corte 2D ----
    bc = meta["corte"]["bounds"]
    liq2 = (pr["corte_mascara"] > 0) & (pr["corte_alpha"].astype(float) < 0.5)
    u2 = np.stack([pr["corte_ux"], pr["corte_uy"]], -1).astype(float)
    campo2 = Campo(u2, liq2, bc[0:4:2], bc[1:4:2])
    yy, xx = np.nonzero(liq2)
    elegidos = RNG.choice(len(xx), size=min(250, len(xx)), replace=False)
    lineas2 = []
    for k in elegidos:
        s = campo2.lo + np.array([xx[k], yy[k]]) * campo2.h
        pts, vel = trazar(campo2, s, paso=0.015)
        if len(pts) >= 15:
            lineas2.append(([[x, y, 0.0] for x, y in pts], vel))
    n2 = exportar(lineas2, d / "lineas_corte.json")
    print(f"{cid}: 3D {n3[0]} lineas / {n3[1]} puntos; corte {n2[0]} lineas / {n2[1]} puntos")
