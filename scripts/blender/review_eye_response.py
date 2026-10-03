"""Isolated iris reflectance comparison; preserve pupil, sclera and alpha."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=bpy.context.scene
s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x=1800;s.render.resolution_y=2200;s.render.resolution_percentage=100;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.29;s.render.border_max_x=.71;s.render.border_min_y=.60;s.render.border_max_y=.76
for mode in ['before','after']:
 if mode=='after':
  for n in bpy.data.materials['EyeSurface'].node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image and n.image.colorspace_settings.name=='sRGB':n.image=bpy.data.images.load(str(ROOT/'assets/eye-response-experiment/eye-brown-lighter.png'),check_existing=True)
  for im in bpy.data.images:
   if im.source=='FILE':
    try:im.pack()
    except:pass
  bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/eye-response-candidate.blend'),compress=True)
 s.render.filepath=str(ROOT/'renders/eye-response-experiment'/(mode+'.png'));bpy.ops.render.render(write_still=True)
