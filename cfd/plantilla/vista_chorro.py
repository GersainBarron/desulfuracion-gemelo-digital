"""Vista del gas cerca de la punta en la prueba con toberas (instante 1 s)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

d = Path(sys.argv[1])
meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
c = np.load(d / "corte.npz")
x0, x1, y0, y1 = meta["corte"]["bounds"][:4]
nx, ny = meta["corte"]["dims"][:2]
X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
m = c["mascara"] > 0
a = np.where(m, np.clip(c["alpha"][-1].astype(float), 1e-4, 1), np.nan)
ux, uy = c["ux"][-1].astype(float), c["uy"][-1].astype(float)
fig, ejes = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)
for ax, (xl, yl), titulo in ((ejes[0], ((x0, x1), (y0, y1)), "olla completa"),
                             (ejes[1], ((-0.6, 0.6), (0.1, 1.3)), "zona de la punta")):
    im = ax.pcolormesh(X, Y, a, cmap="inferno", norm=LogNorm(1e-4, 1), shading="auto")
    liq = m & (a < 0.5)
    ax.streamplot(X, Y, np.where(liq, ux, 0), np.where(liq, uy, 0), color="w", density=1.3, linewidth=0.5, arrowsize=0.6)
    g = meta["geometria"]
    ax.add_patch(plt.Rectangle((-0.1, g["punta_lanza_y_m"]), 0.2, y1, color="0.6"))
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.set_title(titulo)
fig.colorbar(im, ax=ejes, label="fracción de gas (escala log)")
fig.suptitle(f"Prueba con toberas a 45°: t = {c['t'][-1]:g} s, corte z = 0")
fig.savefig(d / "chorro.png", dpi=110)
print(d / "chorro.png")
