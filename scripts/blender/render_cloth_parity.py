"""Reopen the actual GLB in a clean process and render its portable representation.
This verifies export appearance only; it is not a Babylon/browser screenshot.
"""
import bpy,sys,json,math,argparse,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser();parser.add_argument('view',nargs='?',default='portrait',choices=['portrait','three-quarter','full','profile']);parser.add_argument('--samples',type=int,default=96);parser.add_argument('--resolution',type=int,default=900);parser.add_argument('--output');options=parser.parse_args(args);view=options.view
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports/cloth-parity-candidate.glb'))
scene=bpy.context.scene
# Blender's glTF import changes right-handed Y-up back to Blender Z-up.
mesh=[o for o in scene.objects if o.type=='MESH'];arm=[o for o in scene.objects if o.type=='ARMATURE']
report={'sourceGLBSha256':hashlib.sha256((ROOT/'exports/cloth-parity-candidate.glb').read_bytes()).hexdigest(),'verificationType':'Blender Cycles GLB re-import, not browser rendering','objects':[o.name for o in scene.objects],'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials],'morphs':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []} for o in mesh],'skeletons':[{'name':o.name,'bones':len(o.data.bones)} for o in arm],'images':[{'name':im.name,'size':list(im.size)} for im in bpy.data.images if im.source=='FILE']}
(ROOT/'reports/cloth-parity-reopened.json').write_text(json.dumps(report,indent=2))
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
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'renders'/(options.output or ('glb-'+view+'.png')))
import addon_utils;addon_utils.enable('cycles');scene.render.engine='CYCLES';scene.cycles.samples=options.samples;scene.cycles.use_denoising=False
bpy.ops.render.render(write_still=True)
