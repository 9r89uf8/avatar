"""Isolated UV bake that removes narrow photo-derived lid contamination.
No geometry or working-master overwrite; uses the existing licensed base skin.
"""
import bpy,json,sys,math
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'after'
s=bpy.context.scene;b=bpy.data.objects['AvatarBody'];m=bpy.data.materials['Skin'];ns=m.node_tree.nodes;lk=m.node_tree.links;p=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
if mode in ['after','constant','closedmask']:
 j=json.loads((ROOT/'reports/eyelids/rim-correspondence.json').read_text());assert len(b.data.vertices)==j['sourceVertices']
 weights=[0.]*len(b.data.vertices)
 for side in j['sides'].values():
  for part in side.values():
   for key in (['rim_faces','outer_to_next_skin_faces','one_extra_ring_face_candidates'] if mode in ['constant','closedmask'] else ['rim_faces','outer_to_next_skin_faces']):
    for fid in part.get(key,[]):
     for vid in b.data.polygons[fid].vertices:weights[vid]=1.
 if mode=='closedmask':
  keys=b.data.shape_keys.key_blocks
  for name in ['eyeBlinkLeft','eyeBlinkRight']:keys[name].value=1
  sample=b.shape_key_add(name='_closed_color_mask_sample',from_mix=True);positions=[v.co.copy() for v in sample.data];b.shape_key_remove(sample)
  for name in ['eyeBlinkLeft','eyeBlinkRight']:keys[name].value=0
  for i,point in enumerate(positions):
   q=world_to_camera_view(s,s.camera,b.matrix_world@point);x=q.x*1800-.29*1800;y=(1-q.y)*2200-(1-.76)*2200
   if point.y>-.09:continue
   for cx,cy,rx,ry in [(216,196,90,44),(552,200,89,44)]:
    r=math.sqrt(((x-cx)/rx)**2+((y-cy)/ry)**2);weights[i]=max(weights[i],max(0,min(1,(1.14-r)/.22)))
 attr=b.data.color_attributes.new(name='LidDiffuseCleanMask',type='FLOAT_COLOR',domain='POINT')
 for i,w in enumerate(weights):attr.data[i].color=(w,w,w,1)
 if mode in ['constant','closedmask']:
  base=ns.new('ShaderNodeRGB');base.outputs[0].default_value=(.43,.235,.145,1)
 else:
  base=ns.new('ShaderNodeTexImage');base.image=bpy.data.images.load(str(ROOT/'assets/textures/skin-base-tonematched.png'),check_existing=True);base.image.colorspace_settings.name='sRGB'
 attribute=ns.new('ShaderNodeVertexColor');attribute.layer_name=attr.name
 old=p.inputs['Base Color'].links[0].from_socket;mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MIX';lk.new(attribute.outputs['Color'],mix.inputs[0]);lk.new(old,mix.inputs[1]);lk.new(base.outputs['Color'],mix.inputs[2])
 emit=ns.new('ShaderNodeEmission');lk.new(mix.outputs[0],emit.inputs[0]);out=next(n for n in ns if n.type=='OUTPUT_MATERIAL');lk.new(emit.outputs[0],out.inputs['Surface'])
 im=bpy.data.images.new('skin-reference-lidclean-'+mode+'.png',width=4096,height=4096,alpha=False);im.colorspace_settings.name='sRGB';tex=ns.new('ShaderNodeTexImage');tex.image=im;ns.active=tex
 # Preserve original texels outside evaluated/unmasked skin instead of clearing them.
 source_image=next(n.image for n in ns if n.type=='TEX_IMAGE' and n.image and n.image.name!='skin-reference-lidclean-'+mode+'.png' and n.image.colorspace_settings.name=='sRGB' and n.image.size[0]==4096 and 'reference' in n.image.name)
 pixel_copy=np.empty(len(source_image.pixels),dtype=np.float32);source_image.pixels.foreach_get(pixel_copy);im.pixels.foreach_set(pixel_copy);del pixel_copy
 bpy.ops.object.select_all(action='DESELECT');b.select_set(True);bpy.context.view_layer.objects.active=b;s.cycles.samples=1;s.render.bake.margin=16;bpy.ops.object.bake(type='EMIT',margin=16,use_clear=False)
 im.filepath_raw=str(ROOT/'assets/lid-diffuse-experiment'/('skin-reference-lidclean-'+mode+'.png'));im.file_format='PNG';im.save();im.pack()
 lk.new(p.outputs[0],out.inputs['Surface']);lk.new(tex.outputs['Color'],p.inputs['Base Color']);ns.remove(emit);ns.remove(mix);ns.remove(attribute);ns.remove(base);b.data.color_attributes.remove(attr)
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes'/('lid-diffuse-'+mode+'-candidate.blend')),compress=True)
 (ROOT/'reports/lid-diffuse-experiment'/('mask-'+mode+'.json')).write_text(json.dumps({'source':('Existing tonematched CC0 base' if mode=='after' else 'Authored constant linear skin RGB [0.43,0.235,0.145]'),'verticesAtFullMask':sum(w==1 for w in weights),'bodyVertices':len(weights),'mode':mode,'maskDefinition':'Verified rim/outward faces; constant adds one face-ring; closedmask also feathers closing-lid projected regions. See script for exact current-character calibration.'},indent=2))
s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x=1800;s.render.resolution_y=2200;s.render.resolution_percentage=100;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.29;s.render.border_max_x=.71;s.render.border_min_y=.60;s.render.border_max_y=.76
for view in ['neutral','blink']:
 for ob in s.objects:
  if ob.type=='MESH' and ob.data.shape_keys:
   for key in ob.data.shape_keys.key_blocks:
    if key.name in ['eyeBlinkLeft','eyeBlinkRight']:key.value=1 if view=='blink' else 0
 s.render.filepath=str(ROOT/'renders/lid-diffuse-experiment'/(view+'-'+mode+'.png'));bpy.ops.render.render(write_still=True)
