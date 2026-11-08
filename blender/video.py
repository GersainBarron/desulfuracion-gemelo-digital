"""Une una secuencia de PNG en un video MP4 (H.264) con el editor de video de Blender.
Uso: blender -b --factory-startup --python video.py -- <carpeta_png> <salida.mp4> [fps] [prefijo]"""
import sys
from pathlib import Path

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
carpeta, salida = Path(args[0]), Path(args[1])
fps = int(args[2]) if len(args) > 2 else 12
prefijo = args[3] if len(args) > 3 else "cuadro_"
cuadros = sorted(carpeta.glob(f"{prefijo}*.png"))
if not cuadros:
    sys.exit(f"no hay {prefijo}*.png en {carpeta}")

esc = bpy.context.scene
editor = esc.sequence_editor_create()
tiras = editor.strips if hasattr(editor, "strips") else editor.sequences   # Blender 5: "strips"
tira = tiras.new_image(name="cuadros", filepath=str(cuadros[0]), channel=1, frame_start=1)
for c in cuadros[1:]:
    tira.elements.append(c.name)
esc.frame_start, esc.frame_end = 1, len(cuadros)
esc.render.resolution_x, esc.render.resolution_y = 1920, 1080
esc.render.resolution_percentage = 100
esc.render.fps = fps
ims = esc.render.image_settings
if hasattr(ims, "media_type"):
    ims.media_type = "VIDEO"
ims.file_format = "FFMPEG"
esc.render.ffmpeg.format = "MPEG4"
esc.render.ffmpeg.codec = "H264"
esc.render.ffmpeg.constant_rate_factor = "HIGH"
esc.render.filepath = str(salida)
bpy.ops.render.render(animation=True)
print("VIDEO_OK", salida, len(cuadros), "cuadros")
