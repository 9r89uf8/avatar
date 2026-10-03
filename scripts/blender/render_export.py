"""Reopen the actual GLB in a clean process and render its portable representation.
This verifies export appearance only; it is not a Babylon/browser screenshot.
"""
import bpy,sys,json,math,argparse,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser();parser.add_argument('view',nargs='?',default='portrait',choices=['portrait','three-quarter','full','profile']);parser.add_argument('--samples',type=int,default=96);parser.add_argument('--resolution',type=int,default=900);parser.add_argument('--output');parser.add_argument('--expression',choices=['neutral','blink','smile'],default='neutral');parser.add_argument('--head-turn',type=float,default=0);parser.add_argument('--crop-eyes',action='store_true');options=parser.parse_args(args);view=options.view
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports/avatar-uncompressed.glb'))
scene=bpy.context.scene
scene.frame_set(1)
# Stop imported clip evaluation before applying a diagnostic pose; otherwise
# rendering can reevaluate frame1 and silently reset the requested head turn.
for animated in scene.objects:
 if animated.animation_data:animated.animation_data_clear()
bpy.context.view_layer.update()
head_before=None;head_object=None
for ob in scene.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  for key in ob.data.shape_keys.key_blocks:
   if key.name in ['eyeBlinkLeft','eyeBlinkRight']:key.value=1 if options.expression=='blink' else 0
   if key.name in ['mouthSmileLeft','mouthSmileRight']:key.value=.65 if options.expression=='smile' else 0
 if ob.type=='ARMATURE' and 'head' in ob.pose.bones and options.head_turn:
  head=ob.pose.bones['head'];head_before=(ob.matrix_world@head.matrix).to_quaternion();head_object=ob;head.rotation_mode='QUATERNION';axis=(ob.matrix_world.to_3x3()@head.matrix.to_3x3()).inverted()@Vector((0,0,1));head.rotation_quaternion=head.rotation_quaternion@Quaternion(axis.normalized(),math.radians(options.head_turn))
bpy.context.view_layer.update()
# Blender's glTF import changes right-handed Y-up back to Blender Z-up.
mesh=[o for o in scene.objects if o.type=='MESH'];arm=[o for o in scene.objects if o.type=='ARMATURE']
report={'sourceGLBSha256':hashlib.sha256((ROOT/'exports/avatar-uncompressed.glb').read_bytes()).hexdigest(),'verificationType':'Blender Cycles GLB re-import, not browser rendering','pose':{'expression':options.expression,'headTurnDegrees':options.head_turn},'objects':[o.name for o in scene.objects],'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials],'morphs':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []} for o in mesh],'skeletons':[{'name':o.name,'bones':len(o.data.bones)} for o in arm],'images':[{'name':im.name,'size':list(im.size)} for im in bpy.data.images if im.source=='FILE']}
(ROOT/'reports/glb-reopened.json').write_text(json.dumps(report,indent=2))
world=bpy.data.worlds.new('ExportReview');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.28,.32,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3
look=Vector((0,-.015,1.412))
def point(ob,p):ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;point(o,look)
area('Key',(-1.3,-2.0,2.55),175,1.5,(1,.92,.86));area('Fill',(1.6,-.7,1.9),60,1.4,(.81,.88,1));area('Rim',(.3,.9,2.15),35,1,(1,.9,.8))
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);scene.collection.objects.link(cam);cam.location=(0,-1.10,1.492);point(cam,look);camd.lens=90;scene.camera=cam
if view=='three-quarter':cam.location=(.67,-1.08,1.492);camd.lens=90;point(cam,look)
if view=='profile':cam.location=(1.2,-.08,1.492);camd.lens=90;point(cam,look)
if view=='full':cam.location=(.1,-4.15,1);camd.lens=65;point(cam,(0,0,.84))
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.55
scene.render.resolution_x=options.resolution;scene.render.resolution_y=round(options.resolution*11/9);scene.render.resolution_percentage=100
if options.crop_eyes:
 scene.render.resolution_x=1800;scene.render.resolution_y=2200;scene.render.use_border=True;scene.render.use_crop_to_border=True;scene.render.border_min_x=.29;scene.render.border_max_x=.71;scene.render.border_min_y=.60;scene.render.border_max_y=.76
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'renders'/(options.output or ('glb-'+view+'.png')))
import addon_utils;addon_utils.enable('cycles');scene.render.engine='CYCLES';scene.cycles.samples=options.samples;scene.cycles.use_denoising=False
bpy.ops.render.render(write_still=True)
if head_before is not None:
 observed=head_before.rotation_difference((head_object.matrix_world@head_object.pose.bones['head'].matrix).to_quaternion()).angle;report['pose']['observedHeadRotationDegrees']=math.degrees(observed)
 if abs(math.degrees(observed)-abs(options.head_turn))>.2:raise RuntimeError('Diagnostic head pose was reset or differs from requested rotation')
report['renderCompleted']=True;report['renderFile']=scene.render.filepath;report['renderImageSha256']=hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest();report['samples']=options.samples;report['cameraView']=view
(ROOT/'reports/glb-reopened.json').write_text(json.dumps(report,indent=2))
Path(scene.render.filepath).with_suffix('.json').write_text(json.dumps({'type':'GLB re-import in Blender Cycles, not browser screenshot','sourceGLBSha256':report['sourceGLBSha256'],'imageSha256':report['renderImageSha256'],'pose':report['pose'],'view':view,'samples':options.samples},indent=2))
