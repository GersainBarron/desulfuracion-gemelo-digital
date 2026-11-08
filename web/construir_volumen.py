"""Datos 3D del explorador de la pagina: el caso base (c12) y los 9 casos del barrido.

Uso:  python web/construir_volumen.py
Lee   extraccion/<caso>/promedio.npz (velocidad y gas promedio t >= 20 s), meta.json
      y, solo para c12, volumen.npz (gas por instante, para la pluma animada).
Escribe web/datos/vol_<caso>.bin y .json, y web/datos/casos.json con la lista:
  bloque 1  RGBA uint8 [z][y][x]: velocidad del arrabio (R,G,B) y fraccion de gas (A), promedio t >= 20 s
            componente u -> 128 + 127 * signo(u) * sqrt(|u| / UMAX)   (mas resolucion en flujo lento)
            gas a       -> 255 * sqrt(a)
  bloque 2  (solo c12) uint8 [instante][z][y][x], media resolucion vertical: gas sumergido por instante
Solo se conserva el liquido (a < 0.5) bajo la superficie; el espacio libre queda en cero.
"""
import json
from pathlib import Path

import numpy as np

WEB = Path(__file__).resolve().parent
EXT = WEB.parent / "extraccion"
UMAX = 0.75
BARRIDO = ["c04", "c05", "c06", "c07", "c02", "c08", "c09", "c10", "c11"]


def cod_u(v):
    return np.clip(np.round(128 + 127 * np.sign(v) * np.sqrt(np.abs(v) / UMAX)), 0, 255).astype(np.uint8)


def construir(caso, con_serie):
    meta = json.loads((EXT / caso / "meta.json").read_text(encoding="utf-8"))
    G, B = meta["geometria"], meta["volumen"]["bounds"]
    NX, NY, NZ = meta["volumen"]["dims"]
    H = G["altura_bano_m"]
    p = np.load(EXT / caso / "promedio.npz")
    u = p["vol_u"].astype(np.float32)
    a = np.clip(p["vol_alpha"].astype(np.float32), 0, 1)
    m = p["vol_mascara"] > 0
    y = np.linspace(B[2], B[3], NY)[None, :, None]
    liquido = m & (a < 0.5) & (y < H)
    u[~liquido] = 0
    gas = np.where(m & (y < H - 0.03), a, 0)
    rgba = np.concatenate([cod_u(u), np.round(255 * np.sqrt(gas))[..., None].astype(np.uint8)], -1)
    partes, serie_info = [rgba.tobytes()], None
    if con_serie:
        v = np.load(EXT / caso / "volumen.npz")
        t = v["t"]
        sel = np.where(t >= meta["t_promedio_desde_s"])[0]
        s = np.clip(v["alpha"][sel][:, :, ::2, :].astype(np.float32), 0, 1)
        y2 = np.linspace(B[2], B[3], NY)[::2][None, None, :, None]
        s = np.where((v["mascara"][:, ::2, :][None] > 0) & (y2 < H - 0.03), s, 0)
        partes.append(np.round(255 * np.sqrt(s)).astype(np.uint8).tobytes())
        serie_info = {"dims": [s.shape[3], s.shape[2], s.shape[1]], "t": [float(x) for x in t[sel]]}
    (WEB / "datos" / f"vol_{caso}.bin").write_bytes(b"".join(partes))
    pr = meta["parametros"]
    info = {"caso": caso, "bounds": B, "dims": [NX, NY, NZ], "umax": UMAX, "serie": serie_info, "geometria": G,
            "bytes_bloque1": int(rgba.nbytes), "parametros": pr,
            "nota": "promedio temporal desde 20 s; velocidad del arrabio solo en el liquido"}
    (WEB / "datos" / f"vol_{caso}.json").write_text(json.dumps(info), encoding="utf-8")
    vel = np.linalg.norm(u, axis=-1)[liquido]
    print(f"{caso}: {sum(len(x) for x in partes) / 1e6:.2f} MB  lanza {pr['profundidad_lanza_m']} m  gas x{pr['factor_caudal_gas']}"
          f"  |u| p50 {np.median(vel):.4f} p95 {np.percentile(vel, 95):.4f}")
    return {"id": caso, "lanza_m": pr["profundidad_lanza_m"], "gas_x": pr["factor_caudal_gas"],
            "malla": pr.get("malla"), "toberas": bool(pr.get("toberas")), "serie": con_serie}


casos = [construir("c12", True)] + [construir(c, False) for c in BARRIDO]
(WEB / "datos" / "casos.json").write_text(json.dumps(casos, indent=1), encoding="utf-8")
print("casos.json:", len(casos), "casos")
