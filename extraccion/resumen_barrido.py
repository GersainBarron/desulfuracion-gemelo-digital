"""Resumen del barrido a partir del flujo promedio (t >= 20 s) en el corte por las toberas.
Uso: python resumen_barrido.py   ->  imprime la tabla y escribe resumen_barrido.json"""
import json
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
filas = []
for d in sorted(p for p in AQUI.iterdir() if (p / "COMPLETO").exists()):
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    pr = np.load(d / "promedio.npz")
    H = meta["geometria"]["altura_bano_m"]
    y = np.linspace(meta["corte"]["bounds"][2], meta["corte"]["bounds"][3], meta["corte"]["dims"][1])
    bano = (pr["corte_mascara"] > 0) & (pr["corte_alpha"].astype(float) < 0.5) & (y[:, None] < H - 0.2)
    v = np.hypot(pr["corte_ux"].astype(float), pr["corte_uy"].astype(float))[bano]
    gas = pr["vol_alpha"].astype(float)
    vol_liq = (pr["vol_mascara"] > 0) & (gas < 0.5)
    pluma = (gas > 0.001) & vol_liq
    p = meta["parametros"]
    filas.append({"caso": d.name, "malla": p.get("malla"), "caudal_x": p.get("factor_caudal_gas"),
                  "lanza_m": p.get("profundidad_lanza_m"), "v_media_m_s": round(float(v.mean()), 4),
                  "v_p95_m_s": round(float(np.percentile(v, 95)), 4),
                  "pluma_frac_volumen": round(float(pluma.sum() / vol_liq.sum()), 4)})
print(f"{'caso':5s} {'malla':6s} {'Q':>4s} {'lanza':>5s} {'v media':>8s} {'v p95':>7s} {'pluma %':>8s}")
for f in filas:
    print(f"{f['caso']:5s} {f['malla']:6s} {f['caudal_x']:4} {f['lanza_m']:5} {f['v_media_m_s']:8.3f} "
          f"{f['v_p95_m_s']:7.3f} {100 * f['pluma_frac_volumen']:8.1f}")
(AQUI / "resumen_barrido.json").write_text(json.dumps(filas, indent=2, ensure_ascii=False), encoding="utf-8")
