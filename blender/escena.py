"""Escena de la olla en corte con los resultados de la CFD (correr dentro de Blender 5.2).

Uso:
  blender -b --factory-startup --python escena.py -- <caso> [cuadro]       render de un cuadro (prueba)
  blender -b --factory-startup --python escena.py -- <caso> animacion      render de toda la animacion
Lee blender/datos/<caso>/ (de preparar_datos.py). Guarda blender/escena_<caso>.blend y los PNG en
blender/render/<caso>/.
Ejes: CFD (x, y vertical, z) -> Blender (X = x, Y = z, Z = y). Se conserva la mitad trasera (Y >= 0);
la camara mira desde -Y al plano del corte, que es el plano de las dos toberas.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np

AQUI = Path(__file__).resolve().parent
args = sys.argv[sys.argv.index("--") + 1:]
CASO = args[0]
MODO = args[1] if len(args) > 1 else "prueba"
DATOS = AQUI / "datos" / CASO
E = json.loads((DATOS / "escena.json").read_text(encoding="utf-8"))
G = E["geometria"]
R, H, A = G["radio_olla_m"], G["altura_bano_m"], G["medio_lado_lanza_m"]
Y_PUNTA = G["punta_lanza_y_m"]
X0, X1, Z0, Z1 = E["corte_bounds"]
N = E["n_cuadros"]                                 # cuadros de la animacion (con los intermedios)
MURO, FONDO, BORDE = 0.25, 0.25, 3.25          # espesor de refractario y altura del borde de la olla

bpy.ops.wm.read_factory_settings(use_empty=True)
esc = bpy.context.scene


# ---------- materiales ----------
def material(nombre, color, rugosidad=0.7, emision=None, fuerza=0.0):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rugosidad
    if emision:
        p.inputs["Emission Color"].default_value = (*emision, 1)
        p.inputs["Emission Strength"].default_value = fuerza
    return m


def mat_bano():
    """Superficie fundida con costras de escoria (ruido)."""
    m = bpy.data.materials.new("bano")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    ruido = n.new("ShaderNodeTexNoise"); ruido.inputs["Scale"].default_value = 3.5
    ruido.inputs["Detail"].default_value = 8
    rampa = n.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position, rampa.color_ramp.elements[1].position = 0.45, 0.62
    rampa.color_ramp.elements[0].color = (1.0, 0.42, 0.08, 1)        # metal al rojo
    rampa.color_ramp.elements[1].color = (0.05, 0.04, 0.035, 1)      # escoria
    fuerza = n.new("ShaderNodeMath"); fuerza.operation = "MULTIPLY"; fuerza.inputs[1].default_value = 3.2
    inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    l.new(ruido.outputs["Fac"], rampa.inputs["Fac"])
    l.new(rampa.outputs["Color"], p.inputs["Base Color"])
    l.new(rampa.outputs["Color"], p.inputs["Emission Color"])
    l.new(ruido.outputs["Fac"], inv.inputs[1])
    l.new(inv.outputs[0], fuerza.inputs[0])
    l.new(fuerza.outputs[0], p.inputs["Emission Strength"])
    p.inputs["Roughness"].default_value = 0.35
    return m


def mat_corte():
    """Textura del corte (secuencia de imagenes) como emision, transparente donde alfa = 0."""
    m = bpy.data.materials.new("corte")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.remove(n["Principled BSDF"])
    salida = n["Material Output"]
    tex = n.new("ShaderNodeTexImage")
    img = bpy.data.images.load(str(DATOS / "corte_0000.png"))
    img.source = "SEQUENCE"
    tex.image = img
    tex.image_user.frame_duration = N
    tex.image_user.frame_start = 1
    tex.image_user.frame_offset = -1                                  # cuadro 1 -> corte_0000.png
    tex.image_user.use_auto_refresh = True
    tex.interpolation = "Cubic"
    emi = n.new("ShaderNodeEmission"); emi.inputs["Strength"].default_value = 2.2
    tra = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    l.new(tex.outputs["Color"], emi.inputs["Color"])
    l.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    l.new(tra.outputs[0], mix.inputs[1])
    l.new(emi.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], salida.inputs["Surface"])
    return m


REFRACTARIO = material("refractario", (0.20, 0.095, 0.065), 0.9)
ACERO = material("acero", (0.09, 0.09, 0.1), 0.45)
ACERO.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.9
LANZA = material("lanza", (0.38, 0.37, 0.35), 0.8)
BURBUJA = material("burbuja", (0.75, 0.9, 1.0), 0.05, emision=(0.6, 0.85, 1.0), fuerza=0.8)
LINEA = material("linea", (0.85, 0.95, 1.0), 0.5, emision=(0.85, 0.95, 1.0), fuerza=0.45)
BANO, CORTE = mat_bano(), mat_corte()


def objeto(nombre, malla, mat):
    ob = bpy.data.objects.new(nombre, malla)
    esc.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


def girar_perfil(nombre, perfil_rz, mat, pasos=96):
    """Solido de revolucion de medio giro (Y >= 0) a partir de un perfil cerrado en (r, z)."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in perfil_rz]
    cara = bm.faces.new(vs)
    bmesh.ops.spin(bm, geom=[cara] + vs + list(cara.edges), axis=(0, 0, 1), cent=(0, 0, 0),
                   angle=math.pi, steps=pasos, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return objeto(nombre, me, mat)


def caja(nombre, x, y, z, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = ((x[0] + x[1]) / 2 + v.co.x * (x[1] - x[0]), (y[0] + y[1]) / 2 + v.co.y * (y[1] - y[0]),
                (z[0] + z[1]) / 2 + v.co.z * (z[1] - z[0]))
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me); bm.free()
    return objeto(nombre, me, mat)


# ---------- olla, lanza, bano y corte ----------
girar_perfil("olla", [(0, -FONDO), (R + MURO, -FONDO), (R + MURO, BORDE), (R, BORDE), (R, 0), (0, 0)], REFRACTARIO)
CASCO = 0.035                                       # casco de acero por fuera del refractario
girar_perfil("casco", [(0, -FONDO - CASCO), (R + MURO + CASCO, -FONDO - CASCO), (R + MURO + CASCO, BORDE),
                       (R + MURO, BORDE), (R + MURO, -FONDO), (0, -FONDO)], ACERO)
caja("lanza", (-A, A), (0, A), (Y_PUNTA, BORDE + 0.45), LANZA)

bm = bmesh.new()                                    # superficie del bano: medio anillo alrededor de la lanza
vs = [bm.verts.new((A * 1.42, 0, H)), bm.verts.new((R, 0, H))]
borde = bm.edges.new(vs)
bmesh.ops.spin(bm, geom=vs + [borde], axis=(0, 0, 1), cent=(0, 0, 0), angle=math.pi, steps=96)
me = bpy.data.meshes.new("bano"); bm.to_mesh(me); bm.free()
objeto("bano", me, BANO)

me = bpy.data.meshes.new("corte")                   # plano del corte con UV 0..1
me.from_pydata([(X0, 0, Z0), (X1, 0, Z0), (X1, 0, Z1), (X0, 0, Z1)], [], [(0, 1, 2, 3)])
uv = me.uv_layers.new(name="UVMap")
for bucle, (u, v) in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
    bucle.uv = (u, v)
objeto("corte", me, CORTE)


# ---------- lineas de corriente sobre el corte ----------
pts = np.load(DATOS / "lineas_corte.npy")
cortes = np.nonzero(np.isnan(pts[:, 0]))[0]
curva = bpy.data.curves.new("lineas", "CURVE")
curva.dimensions, curva.bevel_depth, curva.bevel_resolution = "3D", 0.0045, 2
inicio = 0
for fin in cortes:
    seg = pts[inicio:fin]
    inicio = fin + 1
    if len(seg) < 4:
        continue
    sp = curva.splines.new("POLY")
    sp.points.add(len(seg) - 1)
    for p, (x, y, _z) in zip(sp.points, seg):
        p.co = (float(x), -0.003, float(y), 1.0)
objeto("lineas_corte", curva, LINEA)


# ---------- burbujas: un objeto por instante, visible solo en su cuadro ----------
def arbol_burbujas():
    t = bpy.data.node_groups.new("burbujas", "GeometryNodeTree")
    t.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    t.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n, l = t.nodes, t.links
    ent, sal = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    esfera = n.new("GeometryNodeMeshIcoSphere"); esfera.inputs["Radius"].default_value = 1.0
    esfera.inputs["Subdivisions"].default_value = 2
    poner_mat = n.new("GeometryNodeSetMaterial"); poner_mat.inputs["Material"].default_value = BURBUJA
    inst = n.new("GeometryNodeInstanceOnPoints")
    radio = n.new("GeometryNodeInputNamedAttribute"); radio.data_type = "FLOAT"
    radio.inputs["Name"].default_value = "radio"
    l.new(esfera.outputs["Mesh"], poner_mat.inputs["Geometry"])
    l.new(ent.outputs[0], inst.inputs["Points"])
    l.new(poner_mat.outputs["Geometry"], inst.inputs["Instance"])
    l.new(radio.outputs["Attribute"], inst.inputs["Scale"])
    l.new(inst.outputs["Instances"], sal.inputs[0])
    return t


ARBOL = arbol_burbujas()
for i in range(N):
    b = np.load(DATOS / f"burbujas_{i:04d}.npy")
    me = bpy.data.meshes.new(f"burbujas_{i:04d}")
    me.from_pydata([(float(x), float(z), float(y)) for x, y, z, _r in b], [], [])
    at = me.attributes.new("radio", "FLOAT", "POINT")
    at.data.foreach_set("value", b[:, 3].astype(np.float32))
    ob = objeto(f"burbujas_{i:04d}", me, None)
    ob.modifiers.new("burbujas", "NODES").node_group = ARBOL
    cuadro = i + 1
    for f, oculto in ((cuadro - 1, True), (cuadro, False), (cuadro + 1, True)):
        ob.hide_render = ob.hide_viewport = oculto
        ob.keyframe_insert("hide_render", frame=f)
        ob.keyframe_insert("hide_viewport", frame=f)


# ---------- camara, luces, mundo y render ----------
foco = bpy.data.objects.new("foco", None); esc.collection.objects.link(foco)
foco.location = (0, 0.35, 1.35)
cam = bpy.data.objects.new("camara", bpy.data.cameras.new("camara")); esc.collection.objects.link(cam)
cam.location, cam.data.lens = (4.9, -6.2, 4.4), 32          # tres cuartos y algo alta: se ve el corte y el bano
cam.data.shift_x, cam.data.shift_y = -0.04, 0.03            # la olla un poco a la derecha y abajo: arriba a la izquierda va el titulo
cam.constraints.new("TRACK_TO").target = foco
esc.camera = cam
for nombre, lugar, energia, tam in (("clave", (-5.0, -4.5, 6.0), 650, 4.0), ("relleno", (6.0, -2.0, 2.5), 160, 3.0),
                                    ("contra", (-1.0, 5.0, 6.5), 500, 3.0)):
    luz = bpy.data.objects.new(nombre, bpy.data.lights.new(nombre, "AREA"))
    luz.data.energy, luz.data.size = energia, tam
    luz.location = lugar
    luz.constraints.new("TRACK_TO").target = foco
    esc.collection.objects.link(luz)
mundo = bpy.data.worlds.new("mundo"); esc.world = mundo
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.013, 0.016, 1)

esc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for dev in prefs.devices:
    dev.use = dev.type == "OPTIX"
esc.cycles.device = "GPU"
esc.cycles.samples = 64
esc.cycles.use_denoising = True
esc.render.resolution_x, esc.render.resolution_y = 1920, 1080
esc.view_settings.view_transform = "Standard"      # colores del mapa de datos sin alterar
esc.frame_start, esc.frame_end = 1, N
esc.render.fps = 24

SALIDA = AQUI / "render" / CASO
SALIDA.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(AQUI / f"escena_{CASO}.blend"))
if MODO == "animacion":
    esc.render.filepath = str(SALIDA / "cuadro_")
    esc.render.use_overwrite = False                # reanudable: los cuadros ya hechos se saltan
    bpy.ops.render.render(animation=True)
else:
    cuadro = int(MODO) if MODO.isdigit() else N // 2
    esc.frame_set(cuadro)
    esc.render.filepath = str(SALIDA / f"prueba_{cuadro:03d}.png")
    bpy.ops.render.render(write_still=True)
print("ESCENA_OK", CASO, MODO)
