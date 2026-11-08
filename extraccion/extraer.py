"""Extrae de un caso terminado los datos para Blender y la web (correr con pvpython).

Uso:  pvpython extraer.py <carpeta_caso> <carpeta_salida>
Salida en <carpeta_salida>:
  corte.npz     corte vertical z = 0 (plano de las dos toberas), por instante:
                alpha[t,y,x] gas, ux/uy[t,y,x] arrabio, mascara[y,x] (0 = lanza o fuera)
  volumen.npz   fraccion de gas en 3D por instante, alpha[t,z,y,x] (para la pluma)
  promedio.npz  promedios temporales desde t_promedio: corte (alpha, ux, uy) y
                volumen (alpha, ux, uy, uz del arrabio) para las lineas de corriente
  meta.json     parametros, tiempos, mallas de muestreo y geometria
Todo en float16 salvo el campo de velocidad promedio 3D (float32).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from paraview.simple import OpenFOAMReader, ResampleToImage
from vtk.numpy_interface import dataset_adapter as dsa

caso, salida = Path(sys.argv[1]), Path(sys.argv[2])
salida.mkdir(parents=True, exist_ok=True)
resumen = json.loads((caso / "resumen_caso.json").read_text())
params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

R, H, LIBRE, A = 1.6, resumen["altura_bano_m"], 0.4, 0.1
YTOP = H + LIBRE
T_PROMEDIO = 20.0
CORTE = dict(bounds=[-R, R, 0.0, YTOP, 0.0, 0.0], dims=[161, 152, 1])
VOLUMEN = dict(bounds=[-R, R, 0.0, YTOP, -R, R], dims=[65, 61, 65])

(caso / "caso.foam").touch()
lector = OpenFOAMReader(FileName=str(caso / "caso.foam"))
lector.MeshRegions = ["internalMesh"]
lector.CellArrays = ["alpha.argon", "U.hierro"]
lector.SkipZeroTime = 0
lector.UpdatePipelineInformation()
tiempos = list(lector.TimestepValues)


def muestreador(cfg):
    r = ResampleToImage(Input=lector)
    r.UseInputBounds = 0
    r.SamplingBounds = cfg["bounds"]
    r.SamplingDimensions = cfg["dims"]
    return r


def leer(r, t, forma):
    r.UpdatePipeline(t)
    d = dsa.WrapDataObject(r.GetClientSideObject().GetOutputDataObject(0)).PointData
    a = np.asarray(d["alpha.argon"]).reshape(forma)
    u = np.asarray(d["U.hierro"]).reshape(forma + (3,))
    m = np.asarray(d["vtkValidPointMask"]).reshape(forma)
    return a, u, m


rc, rv = muestreador(CORTE), muestreador(VOLUMEN)
fc = (CORTE["dims"][1], CORTE["dims"][0])                          # (y, x)
fv = (VOLUMEN["dims"][2], VOLUMEN["dims"][1], VOLUMEN["dims"][0])  # (z, y, x)
nt = len(tiempos)
c_alpha = np.zeros((nt,) + fc, np.float16)
c_ux, c_uy = np.zeros_like(c_alpha), np.zeros_like(c_alpha)
v_alpha = np.zeros((nt,) + fv, np.float16)
suma_c = np.zeros(fc + (3,))
suma_v = np.zeros(fv + (4,))
n_prom = 0
t0 = time.time()
for i, t in enumerate(tiempos):
    a, u, mc = leer(rc, t, fc)
    c_alpha[i], c_ux[i], c_uy[i] = a, u[..., 0], u[..., 1]
    av, uv, mv = leer(rv, t, fv)
    v_alpha[i] = av
    if t >= T_PROMEDIO:
        suma_c += np.stack([a, u[..., 0], u[..., 1]], -1)
        suma_v += np.concatenate([av[..., None], uv], -1)
        n_prom += 1
    if i % 10 == 0:
        print(f"{caso.name}: instante {t:g} ({i + 1}/{nt}) {time.time() - t0:.0f} s", flush=True)

pc, pv = suma_c / max(n_prom, 1), suma_v / max(n_prom, 1)
np.savez_compressed(salida / "corte.npz", t=np.array(tiempos), alpha=c_alpha, ux=c_ux, uy=c_uy,
                    mascara=mc.astype(np.uint8))
np.savez_compressed(salida / "volumen.npz", t=np.array(tiempos), alpha=v_alpha, mascara=mv.astype(np.uint8))
np.savez_compressed(salida / "promedio.npz",
                    corte_alpha=pc[..., 0].astype(np.float16), corte_ux=pc[..., 1].astype(np.float16),
                    corte_uy=pc[..., 2].astype(np.float16), corte_mascara=mc.astype(np.uint8),
                    vol_alpha=pv[..., 0].astype(np.float16), vol_u=pv[..., 1:].astype(np.float32),
                    vol_mascara=mv.astype(np.uint8))
meta = {"caso": caso.name, "parametros": params, "tiempos_s": tiempos, "t_promedio_desde_s": T_PROMEDIO,
        "instantes_promediados": n_prom, "corte": {**CORTE, "plano": "z = 0 (pasa por la lanza y las dos toberas)",
        "orden": "[t, y, x]"}, "volumen": {**VOLUMEN, "orden": "[t, z, y, x]"},
        "geometria": {"radio_olla_m": R, "altura_bano_m": H, "espacio_libre_m": LIBRE,
                      "medio_lado_lanza_m": A, "punta_lanza_y_m": resumen["punta_lanza_y_m"]},
        "caudal_argon_m3_s": resumen["caudal_argon_m3_s"], "segundos_extraccion": round(time.time() - t0)}
(salida / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
(salida / "COMPLETO").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
print(f"{caso.name}: listo en {time.time() - t0:.0f} s", flush=True)
