import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=bpy.context.scene
s.cycles.use_denoising=False;s.cycles.samples=64;s.render.resolution_x=900;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.render.use_border=False;s.render.use_crop_to_border=False
for label in ['before','after']:
 bpy.data.objects['Lashes'].hide_render=(label=='after')
 for name in ['LidCandidate_Lashes','LidCandidate_Wetline']:bpy.data.objects[name].hide_render=(label=='before')
 s.render.filepath=str(ROOT/'renders/eyelids'/('portrait-'+label+'-v3.png'));bpy.ops.render.render(write_still=True)
