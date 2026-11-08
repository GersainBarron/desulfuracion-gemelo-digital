"""Control visual de lineas3d.json: vista lateral (x-y) y superior (x-z). Uso: python vista_lineas.py c01"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

AQUI = Path(__file__).resolve().parent
for cid in sys.argv[1:]:
    d = AQUI / cid
    L = json.loads((d / "lineas3d.json").read_text())["lineas"]
    fig, ejes = plt.subplots(1, 2, figsize=(11, 5.2), constrained_layout=True)
    vmax = np.percentile(np.concatenate([l["v"] for l in L]), 98)
    for ax, (i, j), titulo in ((ejes[0], (0, 1), "lateral (x, y)"), (ejes[1], (0, 2), "superior (x, z)")):
        for l in L:
            p = np.array(l["p"])
            seg = np.stack([p[:-1][:, [i, j]], p[1:][:, [i, j]]], 1)
            lc = LineCollection(seg, array=np.array(l["v"][:-1]), cmap="viridis", linewidths=0.4)
            lc.set_clim(0, vmax)
            ax.add_collection(lc)
        ax.set_xlim(-1.65, 1.65); ax.set_ylim(-1.65 if j == 2 else 0, 1.65 if j == 2 else 3.05)
        ax.set_aspect("equal"); ax.set_title(titulo); ax.set_facecolor("black")
    fig.colorbar(lc, ax=ejes, label="velocidad del arrabio (m/s)")
    fig.suptitle(f"{cid}: {len(L)} líneas de corriente 3D del flujo promedio")
    fig.savefig(d / "control_lineas.png", dpi=110)
    print(d / "control_lineas.png")
