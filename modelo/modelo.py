"""Modelo de desulfuracion de arrabio por inyeccion de polvo.

Reproduce Barron, Hilerio y Medina (2015), ecuaciones 6 a 9, 15 y 16.
Funciones puras, sin dependencias fuera de la biblioteca estandar.
"""
import json
import math
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def cargar_parametros(ruta=AQUI / "parametros.json"):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def velocidad_burbuja(g, rho_M, rho_g, d_b, mu_M):
    """Ec. 9, ley de Stokes: velocidad de ascenso de la burbuja (m/s)."""
    return g * (rho_M - rho_g) * d_b ** 2 / (18.0 * mu_M)


def tiempo_residencia(h_i, v_b):
    """Ec. 8: tiempo medio de residencia de las particulas (s)."""
    return h_i / v_b


def k_cal(beta, t_R, q_CaO, rho_M, d_p, w_M, rho_CaO):
    """Ec. 7: constante cinetica de la cal (1/s)."""
    return 6.0 * beta * t_R * q_CaO * rho_M / (d_p * w_M * rho_CaO)


def azufre(t, k, S0, Se=0.0):
    """Ec. 6: concentracion de azufre en el tiempo (% en peso)."""
    return Se + (S0 - Se) * math.exp(-k * t)


def vida_media(k):
    """Ec. 16: vida media de la reaccion de primer orden (s)."""
    return math.log(2.0) / k


def k_mezcla(composicion_wt, k_polvos, masas_molares):
    """Ec. 15: constante de la mezcla ponderada por fraccion molar."""
    moles = {p: composicion_wt[p] / masas_molares[p] for p in k_polvos}
    total = sum(moles.values())
    return sum(moles[p] / total * k_polvos[p] for p in k_polvos)


def k_cal_desde_tabla(t1):
    """Cadena completa ec. 9 -> 8 -> 7 con los datos de la tabla 1."""
    v_b = velocidad_burbuja(t1["g_m_s2"], t1["rho_M_kg_m3"], t1["rho_g_kg_m3"],
                            t1["d_b_m"], t1["mu_M_kg_ms"])
    t_R = tiempo_residencia(t1["h_i_m"], v_b)
    k = k_cal(t1["beta_m_s"], t_R, t1["q_CaO_kg_s"], t1["rho_M_kg_m3"],
              t1["d_p_m"], t1["w_M_kg"], t1["rho_CaO_kg_m3"])
    return {"v_b": v_b, "t_R": t_R, "k": k}


def constantes_polvos(p):
    """Constantes de la tabla 2; la de la cal sale del propio modelo."""
    k = dict(p["tabla2_k_s"])
    k["CaO"] = k_cal_desde_tabla(p["tabla1"])["k"]
    return k
