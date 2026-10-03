"""Isolated before/after review of authored facial medium-frequency anatomy."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from surface_forms import refine_face_surface
body=bpy.data.objects['AvatarBody'];refine_face_surface(body)
s=bpy.context.scene;s.cycles.samples=96;s.cycles.use_denoising=False
s.render.resolution_x=900;s.render.resolution_y=1100;s.render.filepath=str(ROOT/'renders/face-surface-variant.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/face-surface-variant.blend'),compress=True)
bpy.ops.render.render(write_still=True)
