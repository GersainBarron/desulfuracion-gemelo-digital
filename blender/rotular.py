"""Agrega a cada cuadro renderizado el titulo, el tiempo simulado, la escala de colores, la leyenda
y los creditos. Uso: python rotular.py c12   ->  render/<caso>/rotulado_####.png"""
import json
import sys
from pathlib import Path

import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
cid = sys.argv[1]
E = json.loads((AQUI / "datos" / cid / "escena.json").read_text(encoding="utf-8"))
REN = AQUI / "render" / cid
F = "C:/Windows/Fonts/"
fuente = lambda nombre, t: ImageFont.truetype(F + nombre, t)
TIT, SUB, TXT, CHI, TIEMPO = (fuente("segoeuib.ttf", 40), fuente("segoeui.ttf", 23), fuente("segoeui.ttf", 21),
                              fuente("segoeui.ttf", 17), fuente("segoeuib.ttf", 34))
BLANCO, GRIS, GRIS_OSC = (238, 238, 240), (165, 168, 175), (120, 123, 130)
p = E["parametros"]
gas = "argón por dos toberas a 45°" if E.get("toberas") else "argón por la punta de la lanza"
SUBTITULO = (f"Gemelo digital · olla de 150 t · {gas}\n"
             f"Lanza a {p.get('profundidad_lanza_m', 2.0):g} m · CFD Euler-Euler 3D (OpenFOAM)")
CREDITO = ("Basado en Barrón, Hilerio y Medina (2015), Modeling and Simulation of Hot Metal Desulfurization "
           "by Powder Injection, Open J. Appl. Sci. 5: 295–303 · Gemelo digital: Gersain Barrón")
mapa = LinearSegmentedColormap.from_list("arrabio", E["colores"])
VMAX = E["v_max_m_s"]

# escala de colores (vertical, rapido arriba) — se dibuja una vez
BX, BY, BW, BH = 1758, 330, 26, 420
grad = (np.array([mapa(1 - j / (BH - 1)) for j in range(BH)])[:, :3] * 255).astype(np.uint8)
barra = Image.fromarray(np.repeat(grad[:, None, :], BW, 1), "RGB")


def rotular(img, t):
    d = ImageDraw.Draw(img)
    d.text((56, 40), "Desulfuración de arrabio por inyección de polvo", font=TIT, fill=BLANCO)
    d.text((58, 96), SUBTITULO, font=SUB, fill=GRIS, spacing=6)
    d.text((1864, 44), f"t = {t:5.1f} s", font=TIEMPO, fill=BLANCO, anchor="ra")
    d.text((1864, 90), "tiempo simulado", font=CHI, fill=GRIS, anchor="ra")
    d.text((BX + BW, BY - 56), "Velocidad del arrabio", font=TXT, fill=BLANCO, anchor="ra")
    d.text((BX + BW, BY - 30), "metros por segundo", font=CHI, fill=GRIS, anchor="ra")
    img.paste(barra, (BX, BY))
    d.rectangle((BX - 1, BY - 1, BX + BW, BY + BH), outline=GRIS_OSC)
    for v in np.linspace(0, VMAX, 4):
        y = BY + BH - 1 - (v / VMAX) * (BH - 1)
        d.line((BX - 8, y, BX - 1, y), fill=GRIS, width=2)
        d.text((BX - 14, y), f"{v:.1f}", font=CHI, fill=GRIS, anchor="rm")
    ly = BY + BH + 44                                   # leyenda de simbolos
    d.line((BX - 120, ly, BX - 84, ly), fill=(225, 240, 255), width=3)
    d.text((BX - 74, ly), "Líneas de corriente\n(flujo promedio)", font=CHI, fill=GRIS, anchor="lm", spacing=2)
    d.ellipse((BX - 108, ly + 50, BX - 96, ly + 62), fill=(170, 215, 255))
    d.text((BX - 74, ly + 56), "Burbujas de argón", font=CHI, fill=GRIS, anchor="lm")
    d.text((56, 1046), CREDITO, font=CHI, fill=GRIS_OSC, anchor="lm")
    return img


if len(sys.argv) > 2:                                   # prueba: rotular un solo archivo (cuadro k)
    ruta, k = Path(sys.argv[2]), int(sys.argv[3])
    rotular(Image.open(ruta).convert("RGB"), E["tiempo_cuadro_s"][k - 1]).save(ruta.with_name(ruta.stem + "_rotulado.png"))
    sys.exit(0)
cuadros = sorted(REN.glob("cuadro_*.png"))
for k, ruta in enumerate(cuadros):
    t = E["tiempo_cuadro_s"][min(k, len(E["tiempo_cuadro_s"]) - 1)]
    rotular(Image.open(ruta).convert("RGB"), t).save(REN / f"rotulado_{k + 1:04d}.png")
print(f"{cid}: {len(cuadros)} cuadros rotulados")
