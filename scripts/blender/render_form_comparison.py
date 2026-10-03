"""Fixed grazing-light clay review; isolates geometry from photo color and pores."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
variant=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'before'
s=bpy.context.scene
m=bpy.data.materials['Skin'];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for l in list(m.node_tree.links):
 if l.to_node==p and l.to_socket.name in ['Base Color','Normal','Roughness']:m.node_tree.links.remove(l)
p.inputs['Base Color'].default_value=(.32,.32,.32,1);p.inputs['Roughness'].default_value=.55;p.inputs['Subsurface Weight'].default_value=0
for o in s.objects:
 if o.get('avatar_groom_role') or o.name=='Hair':o.hide_render=True
key=bpy.data.objects['Key'];key.location=(-1.15,-.32,1.82);key.data.energy=100;key.data.size=.7;key.rotation_euler=(Vector((0,-.02,1.43))-key.location).to_track_quat('-Z','Y').to_euler()
bpy.data.objects['Fill'].data.energy=20;bpy.data.objects['Rim'].data.energy=0
s.camera.location=(.25,-1.05,1.49);s.camera.rotation_euler=(Vector((0,-.03,1.445))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=110
s.render.resolution_x=900;s.render.resolution_y=1050;s.cycles.samples=96;s.cycles.use_denoising=False
s.render.filepath=str(ROOT/'renders'/('forms-'+variant+'.png'));bpy.ops.render.render(write_still=True)
