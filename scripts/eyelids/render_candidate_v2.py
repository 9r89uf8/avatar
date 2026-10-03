import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];s=bpy.context.scene;c=s.camera
s.cycles.use_denoising=False;s.cycles.samples=96;s.render.resolution_x=1800;s.render.resolution_y=2200;s.render.resolution_percentage=100;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.29;s.render.border_max_x=.71;s.render.border_min_y=.60;s.render.border_max_y=.76
views=['neutral','three-quarter','blink'];original_matrix=c.matrix_world.copy();original_lens=c.data.lens
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if args:views=args
for view in views:
 c.matrix_world=original_matrix;c.data.lens=original_lens
 if view=='three-quarter':
  target=Vector((0,-.015,1.412));c.location=(.72,-1.09,1.492);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
 for ob in s.objects:
  if ob.type=='MESH' and ob.data.shape_keys:
   for key in ob.data.shape_keys.key_blocks:
    if key.name in ['eyeBlinkLeft','eyeBlinkRight']:key.value=1 if view=='blink' else 0
 for label in ['after']:
  bpy.data.objects['Lashes'].hide_render=(label=='after')
  for name in ['LidCandidate_Lashes','LidCandidate_Wetline']:bpy.data.objects[name].hide_render=(label=='before')
  s.render.filepath=str(ROOT/'renders/eyelids'/(view+'-'+label+'-v2.png'));bpy.ops.render.render(write_still=True)
