import bpy,sys,argparse,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--view',default='portrait');p.add_argument('--output',default='portrait-baseline.png');p.add_argument('--samples',type=int,default=64);p.add_argument('--resolution',type=int,default=900);p.add_argument('--expression',default='neutral');o=p.parse_args(args)
s=bpy.context.scene;s.cycles.use_denoising=False;s.cycles.samples=o.samples;s.render.resolution_x=o.resolution;s.render.resolution_y=round(o.resolution*1.2222)
c=s.camera
if o.expression in ['blink','smile']:
 for ob in bpy.context.scene.objects:
  if ob.type=='MESH' and ob.data.shape_keys:
   for key in ob.data.shape_keys.key_blocks:
    if o.expression=='blink' and key.name in ['eyeBlinkLeft','eyeBlinkRight']:key.value=1
    if o.expression=='smile' and key.name in ['mouthSmileLeft','mouthSmileRight']:key.value=.65
if o.expression=='turn':
 head=bpy.data.objects['AvatarRig'].pose.bones['head'];head.rotation_mode='XYZ';head.rotation_euler[1]=.3
if o.view=='three-quarter':
 target=Vector((0,-.015,1.412));c.location=(.72,-1.09,1.492);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
elif o.view=='full':
 target=Vector((0,0,.84));c.location=(.1,-4.15,1.00);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=65
elif o.view=='profile':
 target=Vector((0,-.015,1.412));c.location=(1.2,-.08,1.49);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(ROOT/'renders'/o.output);bpy.ops.render.render(write_still=True)
Path(s.render.filepath).with_suffix('.json').write_text(json.dumps({'type':'Editable source rendered in Blender Cycles','sourceBlendSha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'imageSha256':hashlib.sha256(Path(s.render.filepath).read_bytes()).hexdigest(),'view':o.view,'expression':o.expression,'samples':o.samples},indent=2))
