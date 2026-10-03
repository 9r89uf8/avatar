"""Temporary render-only cause isolation. Never saves the source scene."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=bpy.context.scene
for o in s.objects:
 if o.type=='MESH' and o.data.shape_keys:
  for n in ['eyeBlinkLeft','eyeBlinkRight']:
   if n in o.data.shape_keys.key_blocks:o.data.shape_keys.key_blocks[n].value=1
s.cycles.use_denoising=False;s.cycles.samples=64;s.render.resolution_x=1800;s.render.resolution_y=2200;s.render.resolution_percentage=100;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.29;s.render.border_max_x=.71;s.render.border_min_y=.60;s.render.border_max_y=.76
m=bpy.data.materials['Skin'];p=m.node_tree.nodes.get('Principled BSDF');lk=m.node_tree.links;cases=[]
def disconnect(name):
 for link in list(lk):
  if link.to_socket==p.inputs[name]:lk.remove(link)
def render(label,note):
 s.render.filepath=str(ROOT/'renders/eyelids'/('blink-isolate-'+label+'.png'));bpy.ops.render.render(write_still=True);cases.append({'label':label,'note':note,'file':str(Path(s.render.filepath).relative_to(ROOT))})
disconnect('Base Color');p.inputs['Base Color'].default_value=(.43,.235,.145,1)
render('constant-color','Skin Base Color constant. Original normal map, roughness, SSS, accessory geometry and lights unchanged.')
disconnect('Normal');disconnect('Coat Normal')
render('constant-color-flat-normal','Same constant Base Color; Principled Normal and Coat Normal disconnected. No normal/bump contribution; roughness map and lash geometry unchanged.')
for name in ['Lashes','LidCandidate_Lashes']:bpy.data.objects[name].hide_render=True
render('flat-normal-no-lashes','Same as previous, with both old and candidate lash geometry hidden from render; isolates lash cast shadows.')
disconnect('Roughness');p.inputs['Roughness'].default_value=.7;p.inputs['Coat Weight'].default_value=0;p.inputs['Subsurface Weight'].default_value=0
render('plain-clay-no-lashes','Same color, no normal/bump, no lash geometry. Roughness constant .7, coat and SSS disabled. Remaining lid surface marks are geometric/light response rather than image-texture inputs or lash shadows.')
(ROOT/'reports/eyelids/blink-cause-cases.json').write_text(json.dumps(cases,indent=2))
