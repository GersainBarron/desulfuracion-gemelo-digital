#!/usr/bin/env python3
"""Genera un caso de OpenFOAM de la olla de desulfuracion a partir del tutorial
twoPhaseEulerFoam/RAS/bubbleColumn.

Uso (con el entorno de OpenFOAM cargado):
    python3 preparar.py <carpeta_caso> <params.json> <nucleos>
params: factor_caudal_gas, profundidad_lanza_m, malla ("gruesa" | "media" | "fina")

Geometria (eje vertical = y, como el tutorial):
  olla cilindrica de radio R; la lanza es un hueco cuadrado central que baja desde
  arriba hasta la punta; el argon entra por la cara de la punta (patch 'inlet'),
  dirigido hacia abajo y hacia los lados a 45 grados, como las dos toberas del articulo.
"""
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

caso, params_ruta, nucleos = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
P = json.loads(params_ruta.read_text())
S = json.loads((Path(__file__).parent / "supuestos.json").read_text())
TUT = Path(os.environ["FOAM_TUTORIALS"]) / "multiphase/twoPhaseEulerFoam/RAS/bubbleColumn"

# ---------- geometria ----------
RHO, MASA = 7100.0, 150000.0
R = S["olla"]["diametro_m"][0] / 2
H = MASA / (RHO * math.pi * R ** 2)                # altura del bano
LIBRE = S["olla"]["espacio_libre_m"][0]
A = S["lanza"]["lado_seccion_m"][0] / 2            # medio lado de la lanza
h_i = float(P.get("profundidad_lanza_m", 2.0))
Y_PUNTA = H - h_i
assert 0.05 < Y_PUNTA < H, "la punta de la lanza debe quedar dentro del bano"

# ---------- caudal de argon (articulo) ----------
A_TOBERA = math.pi * (S["lanza"]["diametro_tobera_m"][0] / 2) ** 2
Q = 2 * A_TOBERA * S["lanza"]["velocidad_gas_m_s"][0] * float(P.get("factor_caudal_gas", 1.0))
VN = Q / (2 * A) ** 2                              # componente normal en la cara de la punta

# ---------- toberas reales (opcional) ----------
# Dos toberas en la punta, a x = +-X_TOBERA, apuntando hacia abajo y afuera a 45 grados (articulo:
# vx = -+0.5613, vy = -0.5613). Una tobera inclinada de diametro d corta la cara horizontal de la
# punta en una elipse de area A_TOBERA / cos 45, alargada en x; se aproxima con las caras de la malla
# que caen en esa elipse. El resto de la punta es pared. La velocidad se ajusta para conservar Q.
TOBERAS = bool(P.get("toberas", False))
X_TOBERA = 0.0625
SEMI_X = S["lanza"]["diametro_tobera_m"][0] / 2 / math.cos(math.radians(45))
SEMI_Z = S["lanza"]["diametro_tobera_m"][0] / 2

MALLAS = {"gruesa": (8, 16, 6, 24, 4), "media": (16, 32, 12, 48, 8), "fina": (24, 48, 18, 72, 12)}
NT, NR, NZ0, NZ1, NZ2 = MALLAS[P.get("malla", "media")]


def sh(cmd):
    r = subprocess.run(cmd, shell=True, cwd=caso, capture_output=True, text=True)
    (caso / f"log.{cmd.split()[0]}").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        sys.exit(f"fallo: {cmd}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r.stdout


# ---------- malla O-grid con la lanza como hueco central ----------
NIVELES = [0.0, Y_PUNTA, H, H + LIBRE]
DY = 2.0 / NZ1
NZ = [max(3, round((NIVELES[k + 1] - NIVELES[k]) / DY)) for k in range(3)]
ANG = [225, 315, 45, 135]                          # esquinas en el plano x-z


def vertices():
    v = []
    for y in NIVELES:
        v += [(-A, y, -A), (A, y, -A), (A, y, A), (-A, y, A)]
        v += [(R * math.cos(math.radians(t)), y, R * math.sin(math.radians(t))) for t in ANG]
    return v


def sq(L, i):
    return 8 * L + i


def ci(L, i):
    return 8 * L + 4 + i


def blockmesh():
    bloques, aristas = [], []
    pared, salida, lanza = [], [], []
    for L in range(3):
        for i in range(4):
            j = (i + 1) % 4
            bloques.append(f"hex ({sq(L,i)} {sq(L,j)} {ci(L,j)} {ci(L,i)} "
                           f"{sq(L+1,i)} {sq(L+1,j)} {ci(L+1,j)} {ci(L+1,i)}) ({NT} {NR} {NZ[L]}) simpleGrading (1 1 1)")
            pared.append(f"({ci(L,j)} {ci(L,i)} {ci(L+1,i)} {ci(L+1,j)})")
            if L == 0:
                pared.append(f"({sq(0,i)} {sq(0,j)} {ci(0,j)} {ci(0,i)})")
            if L == 2:
                salida.append(f"({sq(3,i)} {sq(3,j)} {ci(3,j)} {ci(3,i)})")
            if L >= 1:
                lanza.append(f"({sq(L,i)} {sq(L+1,i)} {sq(L+1,j)} {sq(L,j)})")
    # nucleo solo debajo de la punta de la lanza
    bloques.append(f"hex ({sq(0,0)} {sq(0,3)} {sq(0,2)} {sq(0,1)} {sq(1,0)} {sq(1,3)} {sq(1,2)} {sq(1,1)}) "
                   f"({NT} {NT} {NZ[0]}) simpleGrading (1 1 1)")
    pared.append(f"({sq(0,0)} {sq(0,1)} {sq(0,2)} {sq(0,3)})")
    entrada = [f"({sq(1,0)} {sq(1,3)} {sq(1,2)} {sq(1,1)})"]
    for L in range(4):
        y = NIVELES[L]
        for i in range(4):
            j = (i + 1) % 4
            t = math.radians(ANG[i] + 45)
            aristas.append(f"arc {ci(L,i)} {ci(L,j)} ({R*math.cos(t):.6f} {y:.6f} {R*math.sin(t):.6f})")
    vs = "\n".join(f"    ({x:.6f} {y:.6f} {z:.6f})" for x, y, z in vertices())
    def patch(nombre, tipo, caras):
        return f"    {nombre}\n    {{\n        type {tipo};\n        faces\n        (\n            " \
               + "\n            ".join(caras) + "\n        );\n    }\n"
    return ("FoamFile { version 2.0; format ascii; class dictionary; object blockMeshDict; }\n"
            "scale 1;\nvertices\n(\n" + vs + "\n);\nblocks\n(\n    " + "\n    ".join(bloques)
            + "\n);\nedges\n(\n    " + "\n    ".join(aristas) + "\n);\nboundary\n(\n"
            + patch("punta" if TOBERAS else "inlet", "wall" if TOBERAS else "patch", entrada)
            + patch("outlet", "patch", salida)
            + patch("walls", "wall", pared + lanza) + ");\n"
            "// ************************************************************************* //\n")


# ---------- diccionarios ----------
CAB = "FoamFile {{ version 2.0; format ascii; class dictionary; object {}; }}\n"
PIE = "\n// ************************************************************************* //\n"
T_K = S["temperatura_K"][0]


def termo(nombre, eos, cuerpo):
    return CAB.format(nombre) + f"""thermoType
{{ type heRhoThermo; mixture pureMixture; transport const; thermo {cuerpo[0]};
  equationOfState {eos}; specie specie; energy sensibleInternalEnergy; }}
mixture
{{
{cuerpo[1]}
}}""" + PIE


ARGON = termo("thermophysicalProperties.argon", "perfectGas", ("hConst", f"""    specie {{ molWeight {S['argon']['masa_molar_g_mol'][0]}; }}
    thermodynamics {{ Cp {S['argon']['Cp_J_kgK'][0]}; Hf 0; }}
    transport {{ mu {S['argon']['viscosidad_Pa_s'][0]}; Pr 0.67; }}"""))
HIERRO = termo("thermophysicalProperties.hierro", "perfectFluid", ("eConst", f"""    specie {{ molWeight 55.85; }}
    equationOfState {{ R 1e5; rho0 {RHO}; }}
    thermodynamics {{ Cv {S['arrabio']['Cv_J_kgK'][0]}; Hf 0; }}
    transport {{ mu {S['arrabio']['viscosidad_Pa_s'][0]}; Pr {S['arrabio']['Pr'][0]}; }}"""))

CONTROL = CAB.format("controlDict") + """application     twoPhaseEulerFoam;
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         60;
deltaT          0.001;
writeControl    adjustableRunTime;
writeInterval   1;
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   12;
runTimeModifiable yes;
adjustTimeStep  yes;
maxCo           0.5;
maxDeltaT       0.05;
""" + PIE

SETFIELDS = CAB.format("setFieldsDict") + f"""defaultFieldValues ( volScalarFieldValue alpha.argon 0 );
regions
(
    boxToCell
    {{
        box ({-2*R} {H} {-2*R}) ({2*R} {H + 2*LIBRE} {2*R});
        fieldValues ( volScalarFieldValue alpha.argon 1 );
    }}
);""" + PIE

DECOMP = CAB.format("decomposeParDict") + f"numberOfSubdomains {nucleos};\nmethod scotch;" + PIE

def entradas(vx, vy):
    """Condiciones de la entrada de gas: velocidad (sign(x)*vx, -vy, 0), hacia afuera y abajo."""
    return {
        "alpha.argon": "type fixedValue; value uniform 1;",
        "U.argon": f"type exprFixedValue; value uniform (0 {-vy:.6g} 0); "
                   f"valueExpr \"vector(sign(pos().x())*{vx:.6g}, {-vy:.6g}, 0)\";",
        "U.hierro": "type fixedValue; value uniform (0 0 0);",
        "k.argon": f"type fixedValue; value uniform {S['turbulencia']['k_entrada'][0]};",
        "k.hierro": f"type fixedValue; value uniform {S['turbulencia']['k_entrada'][0]};",
        "epsilon.argon": f"type fixedValue; value uniform {S['turbulencia']['epsilon_entrada'][0]};",
        "epsilon.hierro": f"type fixedValue; value uniform {S['turbulencia']['epsilon_entrada'][0]};",
    }


def caja(xc):
    return (f"({xc - SEMI_X:.6f} {Y_PUNTA - 0.005:.6f} {-SEMI_Z:.6f}) "
            f"({xc + SEMI_X:.6f} {Y_PUNTA + 0.005:.6f} {SEMI_Z:.6f})")


TOPOSET = CAB.format("topoSetDict") + f"""actions
(
    {{ name toberas; type faceSet; action new; source boxToFace; box {caja(X_TOBERA)}; }}
    {{ name toberas; type faceSet; action add; source boxToFace; box {caja(-X_TOBERA)}; }}
    {{ name toberas; type faceSet; action subset; source patchToFace; patch punta; }}
);""" + PIE

CREATEPATCH = CAB.format("createPatchDict") + """pointSync false;
patches
(
    { name inlet; patchInfo { type patch; } constructFrom set; set toberas; }
);""" + PIE


# ---------- armado ----------
def renombrar(texto):
    texto = re.sub(r"(?<![A-Za-z])air(?![A-Za-z])", "argon", texto)
    return re.sub(r"(?<![A-Za-z])water(?![A-Za-z])", "hierro", texto)


def cambiar_entrada(texto, nuevo):
    return re.sub(r"(\binlet\s*\{)[^{}]*(\})", lambda m: f"{m.group(1)}\n        {nuevo}\n    {m.group(2)}",
                  texto, count=1)


def armar():
    shutil.rmtree(caso, ignore_errors=True)
    caso.mkdir(parents=True)
    for sub, dest in (("0.orig", "0"), ("constant", "constant"), ("system", "system")):
        for f in (TUT / sub).iterdir():
            (caso / dest).mkdir(exist_ok=True)
            (caso / dest / renombrar(f.name)).write_text(renombrar(f.read_text()))
    c, s0 = caso / "constant", caso / "0"
    fase = c / "phaseProperties"
    t = fase.read_text()
    t = re.sub(r"diameterModel\s+isothermal;\s*isothermalCoeffs\s*\{[^}]*\}",
               f"diameterModel constant;\n    constantCoeffs {{ d {S['argon']['diametro_burbuja_m'][0]}; }}", t)
    t = re.sub(r"\(argon and hierro\)\s+[\d.eE+-]+", f"(argon and hierro) {S['interfase']['tension_superficial_N_m'][0]}", t)
    fase.write_text(t)
    (c / "thermophysicalProperties.argon").write_text(ARGON)
    (c / "thermophysicalProperties.hierro").write_text(HIERRO)
    (caso / "system" / "controlDict").write_text(CONTROL)
    (caso / "system" / "setFieldsDict").write_text(SETFIELDS)
    (caso / "system" / "decomposeParDict").write_text(DECOMP)
    (caso / "system" / "blockMeshDict").write_text(blockmesh())
    extra = {}
    if TOBERAS:
        # la malla se modifica sin campos presentes, para que createPatch no los toque
        s0.rename(caso / "0.campos")
        sh("blockMesh")
        (caso / "system" / "topoSetDict").write_text(TOPOSET)
        (caso / "system" / "createPatchDict").write_text(CREATEPATCH)
        sh("topoSet")
        sh("createPatch -overwrite")
        (caso / "0.campos").rename(s0)
        frontera = (c / "polyMesh" / "boundary").read_text()
        n_caras = int(re.search(r"\binlet\s*\{[^}]*nFaces\s+(\d+);", frontera).group(1))
        area = n_caras * (2 * A / NT) ** 2               # caras del bloque central: uniformes
        vy = Q / area                                    # caudal del articulo por la cara horizontal
        vx = vy                                          # 45 grados
        for f in s0.iterdir():                           # el resto de la punta es pared
            f.write_text(re.sub(r"^(\s*)walls(\s*\{)", r'\1"(walls|punta)"\2', f.read_text(), flags=re.M))
        extra = {"toberas": True, "caras_por_tobera": n_caras // 2, "area_salida_m2": area,
                 "area_elipse_teorica_m2": 2 * math.pi * SEMI_X * SEMI_Z,
                 "velocidad_tobera_m_s": [round(vx, 4), round(-vy, 4)], "rapidez_m_s": round(math.hypot(vx, vy), 4)}
    else:
        sh("blockMesh")
        vx, vy = VN, VN
    for campo, bc in entradas(vx, vy).items():
        f = s0 / campo
        f.write_text(cambiar_entrada(f.read_text(), bc))
    for f in s0.glob("T.*"):
        f.write_text(re.sub(r"uniform\s+[\d.eE+-]+", f"uniform {T_K}", f.read_text()))
    chequeo = sh("checkMesh")
    sh("setFields")
    if nucleos > 1:
        sh("decomposePar -force")
    celdas = re.search(r"cells:\s+(\d+)", chequeo)
    resumen = {"celdas": int(celdas.group(1)) if celdas else None, "malla_ok": "Mesh OK" in chequeo,
               "altura_bano_m": round(H, 3), "punta_lanza_y_m": round(Y_PUNTA, 3),
               "caudal_argon_m3_s": Q, "velocidad_normal_punta_m_s": VN, "celdas_axiales": NZ, **extra}
    (caso / "resumen_caso.json").write_text(json.dumps(resumen, indent=2))
    print(json.dumps(resumen, indent=2))


armar()
