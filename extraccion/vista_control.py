"""Imagen de control de un caso extraido: corte promedio (gas + velocidad del arrabio
con lineas de corriente) y un instante. Uso: python vista_control.py c01 [c02 ...]"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = Path(__file__).resolve().parent
for cid in sys.argv[1:]:
    d = AQUI / cid
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    p, c = np.load(d / "promedio.npz"), np.load(d / "corte.npz")
    x0, x1, y0, y1 = meta["corte"]["bounds"][:4]
    nx, ny = meta["corte"]["dims"][:2]
    X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
    m = p["corte_mascara"] > 0
    liquido = m & (p["corte_alpha"].astype(float) < 0.5)      # la velocidad del arrabio solo tiene sentido en el liquido
    ux, uy = [np.where(liquido, p[k].astype(float), np.nan) for k in ("corte_ux", "corte_uy")]
    vel = np.hypot(ux, uy)
    fig, ejes = plt.subplots(1, 3, figsize=(15, 5.2), constrained_layout=True)
    g = meta["geometria"]
    def olla(ax):
        ax.axhline(g["altura_bano_m"], color="w", lw=0.8, ls="--")
        ax.add_patch(plt.Rectangle((-g["medio_lado_lanza_m"], g["punta_lanza_y_m"]), 2 * g["medio_lado_lanza_m"],
                                   y1 - g["punta_lanza_y_m"], color="0.6"))
        ax.set_aspect("equal"); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_xlabel("x (m)")
    im = ejes[0].pcolormesh(X, Y, np.where(m, p["corte_alpha"].astype(float), np.nan), cmap="inferno",
                            vmin=0, vmax=0.05, shading="auto")
    fig.colorbar(im, ax=ejes[0], label="fracción de gas (promedio)"); olla(ejes[0])
    ejes[0].set_title("Pluma de argón, promedio"); ejes[0].set_ylabel("y (m)")
    im = ejes[1].pcolormesh(X, Y, vel, cmap="viridis", vmin=0, vmax=np.nanpercentile(vel, 99), shading="auto")
    ejes[1].streamplot(X, Y, np.nan_to_num(ux), np.nan_to_num(uy), color="w", density=1.4, linewidth=0.6, arrowsize=0.6)
    fig.colorbar(im, ax=ejes[1], label="velocidad del arrabio (m/s)"); olla(ejes[1])
    ejes[1].set_title("Recirculación del arrabio, promedio")
    k = len(c["t"]) // 2
    im = ejes[2].pcolormesh(X, Y, np.where(m, c["alpha"][k].astype(float), np.nan), cmap="inferno",
                            vmin=0, vmax=0.2, shading="auto")
    fig.colorbar(im, ax=ejes[2], label="fracción de gas"); olla(ejes[2])
    ejes[2].set_title(f"Instante t = {c['t'][k]:g} s")
    pr = meta["parametros"]
    fig.suptitle(f"{cid}: caudal ×{pr.get('factor_caudal_gas')}, lanza {pr.get('profundidad_lanza_m')} m, "
                 f"malla {pr.get('malla')} — corte z = 0 por las toberas", fontsize=12)
    fig.savefig(d / "control.png", dpi=110)
    print(d / "control.png", "gas max prom", float(np.nanmax(p["corte_alpha"])), "vel p99", float(np.nanpercentile(vel, 99)))
