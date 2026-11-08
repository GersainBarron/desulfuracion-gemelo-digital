"""Valida el modelo contra los valores publicados y genera los datos de las figuras 5, 6 y 7.

Uso:  python validar.py      (sale con codigo 1 si alguna comprobacion falla)
Salida: validacion.json y figuras.json en esta carpeta.
"""
import json
import sys

import modelo as m

p = m.cargar_parametros()
t1, val = p["tabla1"], p["validacion"]
S0, T = val["S0_wt"], val["t_inyeccion_s"]
cad = m.k_cal_desde_tabla(t1)
k = m.constantes_polvos(p)

# (nombre, calculado, publicado, tolerancia relativa)
pruebas = [
    ("v_b (m/s)", cad["v_b"], 0.7938, 1e-3),
    ("t_R (s)", cad["t_R"], 2.52, 2e-3),
    ("k_CaO (1/s)", cad["k"], 0.001684, 1e-3),
    ("S final CaO (%)", m.azufre(T, k["CaO"], S0), 0.00176, 2e-2),
    ("S final Mg (%)", m.azufre(T, k["Mg"], S0), 0.0002863, 2e-2),
]
for mz in p["tabla3_mezclas_wt"]:
    km = m.k_mezcla(mz, k, p["masas_molares_g_mol"])
    pruebas.append((f"k_m mezcla {mz['mezcla']} (1/s)", km, mz["km_articulo"], 1e-3))

resultados, fallas = [], 0
for nombre, calc, pub, tol in pruebas:
    ok = abs(calc - pub) <= tol * abs(pub)
    fallas += not ok
    resultados.append({"prueba": nombre, "calculado": calc, "publicado": pub, "ok": ok})
    print(f"{'OK ' if ok else 'FALLA'}  {nombre:28s} calc={calc:.6g}  pub={pub:.6g}")

tiempos = [i * 20.0 for i in range(int(T / 20) + 1)]
fig5 = {p_: [m.azufre(t, k[p_], S0) for t in tiempos] for p_ in ("CaO", "CaC2", "Mg")}
fig6, fig7 = {}, []
for mz in p["tabla3_mezclas_wt"]:
    km = m.k_mezcla(mz, k, p["masas_molares_g_mol"])
    fig6[f"mezcla_{mz['mezcla']}"] = [m.azufre(t, km, S0) for t in tiempos]
    fig7.append({"CaO_wt": mz["CaO"], "vida_media_s": m.vida_media(km), "k_m": km})

json.dump({"cadena": cad, "k_polvos": k, "pruebas": resultados},
          open("validacion.json", "w", encoding="utf-8"), indent=2)
json.dump({"t_s": tiempos, "figura5": fig5, "figura6": fig6, "figura7": fig7},
          open("figuras.json", "w", encoding="utf-8"))
print(f"\n{len(pruebas) - fallas}/{len(pruebas)} comprobaciones correctas")
sys.exit(1 if fallas else 0)
