"""Prepara los datos de un caso para la escena de Blender.

Uso: python preparar_datos.py c03 [subcuadros]
La CFD guarda un instante por segundo; para una animacion fluida se generan SUB cuadros por
segundo interpolando linealmente en el tiempo los campos del corte.
Salida en blender/datos/<caso>/:
  corte_####.png    textura del corte por cuadro (RGBA, 8x la resolucion de la CFD):
                    color = rapidez del arrabio (0 a V_MAX m/s); transparente en el gas y en la lanza
  burbujas_####.npy burbujas por cuadro: x, y, z (CFD), radio (m). Cada burbuja conserva su
                    identidad: nace donde hay gas y avanza con el arrabio mas su ascenso relativo
  lineas_corte.npy  lineas de corriente del flujo promedio sobre el corte (separadas por NaN)
  escena.json       geometria, tiempo de cada cuadro y parametros
"""
import json
import sys
from pathlib import Path

import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

PROY = Path(__file__).resolve().parents[1]
cid = sys.argv[1]
SUB = int(sys.argv[2]) if len(sys.argv) > 2 else 4
EXT, SAL = PROY / "extraccion" / cid, PROY / "blender" / "datos" / cid
SAL.mkdir(parents=True, exist_ok=True)
for viejo in list(SAL.glob("corte_*.png")) + list(SAL.glob("burbujas_*.npy")):
    viejo.unlink()
meta = json.loads((EXT / "meta.json").read_text(encoding="utf-8"))
c = np.load(EXT / "corte.npz")
x0, x1, y0, y1 = meta["corte"]["bounds"][:4]
nx, ny = meta["corte"]["dims"][:2]
H = meta["geometria"]["altura_bano_m"]
ESC, V_MAX = 8, 0.30
V_ASCENSO = 0.25            # velocidad relativa de la burbuja respecto al arrabio (m/s), solo visual
RNG = np.random.default_rng(1)
# Paleta de metal al rojo: lento = rojo oscuro, rapido = amarillo claro (monotona en luminosidad).
COLORES = [(0.30, 0.02, 0.0), (0.72, 0.10, 0.0), (0.98, 0.38, 0.02), (1.0, 0.72, 0.16), (1.0, 0.95, 0.62)]
mapa = LinearSegmentedColormap.from_list("arrabio", COLORES)
mascara = c["mascara"].astype(float)
dx, dy = (x1 - x0) / (nx - 1), (y1 - y0) / (ny - 1)
xs, ys = np.linspace(x0, x1, nx), np.linspace(y0, y1, ny)
T = c["t"].astype(float)
A_ = c["alpha"].astype(np.float32)
UX, UY = c["ux"].astype(np.float32), c["uy"].astype(np.float32)


def subir(campo):
    """Interpola el campo a 8x con bicubico (la imagen va con la fila 0 arriba)."""
    img = Image.fromarray(np.flipud(campo).astype(np.float32), mode="F")
    return np.asarray(img.resize((nx * ESC, ny * ESC), Image.BICUBIC))


def en_tiempo(i, f):
    """Campos del corte entre el instante i y el i+1 (f en [0, 1))."""
    j = min(i + 1, len(T) - 1)
    mezcla = lambda X: (1 - f) * X[i] + f * X[j]
    return mezcla(A_), mezcla(UX), mezcla(UY), (1 - f) * T[i] + f * T[j]


def muestrear(campo, px, py):
    """Interpolacion bilineal de un campo del corte en puntos (x, y)."""
    fx = np.clip((px - x0) / dx, 0, nx - 1.001)
    fy = np.clip((py - y0) / dy, 0, ny - 1.001)
    i, j = fx.astype(int), fy.astype(int)
    wx, wy = fx - i, fy - j
    return ((1 - wx) * (1 - wy) * campo[j, i] + wx * (1 - wy) * campo[j, i + 1]
            + (1 - wx) * wy * campo[j + 1, i] + wx * wy * campo[j + 1, i + 1])


# ---------- cuadros: textura del corte + burbujas que siguen al flujo ----------
m_alta = subir(mascara) > 0.5
bajo_superficie = ys[:, None] < H - 0.08            # la franja de la superficie es interfase, no burbujas
NACER_POR_S = 400                                     # burbujas nuevas por segundo simulado (visual)
burb = np.zeros((0, 4), np.float32)                   # x, y, z, radio
cuadros_t = []
k = 0
for i in range(len(T) - 1):
    for s in range(SUB):
        a, ux, uy, t = en_tiempo(i, s / SUB)
        cuadros_t.append(float(t))
        v = np.hypot(ux, uy)
        rgba = mapa(np.clip(subir(v) / V_MAX, 0, 1))
        rgba[..., 3] = np.where(m_alta & (subir(a) < 0.5), 1.0, 0.0)
        Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").save(SAL / f"corte_{k:04d}.png")
        # avanzar las burbujas existentes hasta este cuadro (RK2, pasos de 0.05 s)
        if k > 0:
            dt_total = t - cuadros_t[-2]
            pasos = max(1, int(np.ceil(dt_total / 0.05)))
            h = dt_total / pasos
            for _ in range(pasos):
                vx1 = muestrear(ux, burb[:, 0], burb[:, 1])
                vy1 = muestrear(uy, burb[:, 0], burb[:, 1]) + V_ASCENSO
                mx, my = burb[:, 0] + 0.5 * h * vx1, burb[:, 1] + 0.5 * h * vy1
                burb[:, 0] += h * muestrear(ux, mx, my)
                burb[:, 1] += h * (muestrear(uy, mx, my) + V_ASCENSO)
            vivas = ((burb[:, 1] < H - 0.03) & (burb[:, 0] > x0) & (burb[:, 0] < x1)
                     & (muestrear(mascara, burb[:, 0], burb[:, 1]) > 0.5)
                     & (muestrear(a, burb[:, 0], burb[:, 1]) < 0.5))
            burb = burb[vivas]
        # nacen burbujas nuevas donde hay gas, en proporcion a la fraccion de gas
        peso = np.where((mascara > 0) & (a > 0.01) & (a < 0.5) & bajo_superficie, a, 0.0).ravel()
        dt_n = (t - cuadros_t[-2]) if k > 0 else 1.0 / SUB
        n_nuevas = RNG.poisson(NACER_POR_S * dt_n) if peso.sum() > 0 else 0
        if n_nuevas:
            idx = RNG.choice(peso.size, n_nuevas, p=peso / peso.sum())
            jj, ii = np.unravel_index(idx, (ny, nx))
            nuevas = np.stack([xs[ii] + RNG.uniform(-0.5, 0.5, n_nuevas) * dx,
                               ys[jj] + RNG.uniform(-0.5, 0.5, n_nuevas) * dy,
                               -RNG.uniform(0.004, 0.035, n_nuevas),        # frente al corte
                               RNG.uniform(0.003, 0.008, n_nuevas)], 1).astype(np.float32)
            burb = np.concatenate([burb, nuevas])
        np.save(SAL / f"burbujas_{k:04d}.npy", burb)
        k += 1
N_CUADROS = k


# ---------- lineas de corriente del flujo promedio ----------
lineas = json.loads((EXT / "lineas_corte.json").read_text())["lineas"]
# Pocas lineas y cortas: guian la vista sin tapar el campo. Se eligen repartidas por el corte
# (la semilla de cada linea es su punto central) y se recortan a ~1.5 m de recorrido.
centros = np.array([l["p"][len(l["p"]) // 2][:2] for l in lineas])
elegidas, minimo = [], 0.32
for kk in RNG.permutation(len(lineas)):
    if all(np.hypot(*(centros[kk] - centros[j])) > minimo for j in elegidas):
        elegidas.append(kk)
partes = []
for kk in elegidas:
    p = np.array(lineas[kk]["p"], dtype=np.float32)
    medio, mitad = len(p) // 2, 50                      # paso de 1.5 cm: 100 puntos = 1.5 m
    p = p[max(0, medio - mitad): medio + mitad][::2]
    if len(p) >= 4:
        partes += [p, np.full((1, 3), np.nan, np.float32)]
np.save(SAL / "lineas_corte.npy", np.concatenate(partes))

escena = {"caso": cid, "parametros": meta["parametros"], "subcuadros_por_instante": SUB,
          "n_cuadros": N_CUADROS, "tiempo_cuadro_s": cuadros_t, "tiempos_s": [float(t) for t in T],
          "corte_bounds": [x0, x1, y0, y1], "v_max_m_s": V_MAX, "colores": COLORES,
          "geometria": meta["geometria"], "toberas": bool(meta["parametros"].get("toberas", False))}
(SAL / "escena.json").write_text(json.dumps(escena, indent=2, ensure_ascii=False), encoding="utf-8")
n_b = [len(np.load(SAL / f"burbujas_{q:04d}.npy")) for q in (0, N_CUADROS // 2, N_CUADROS - 1)]
print(f"{cid}: {N_CUADROS} cuadros ({SUB} por segundo simulado), burbujas en 3 cuadros: {n_b}, "
      f"lineas: {len(elegidas)} de {len(lineas)}")
