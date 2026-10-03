"""Make a standalone glTF derivative. Never overwrite the editable source."""
import bpy,sys,json,hashlib,shutil,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));from bootstrap import load_mpfb
load_mpfb()
from bl_ext.avatar.mpfb.services.exportservice import ExportService
from bl_ext.avatar.mpfb.services.targetservice import TargetService
scene=bpy.context.scene;body=bpy.data.objects['AvatarBody'];rig=bpy.data.objects['AvatarRig']
from cloth_export_parity import capture_cloth_surface,match_cloth_surface
# Capture the desired posed garment before changing modifier evaluation order.
cloth_targets=capture_cloth_surface(scene)
armature_flags=[]
for ob in scene.objects:
 for modifier in ob.modifiers:
  if modifier.type=='ARMATURE':
   armature_flags.append((modifier,modifier.show_viewport,modifier.show_render));modifier.show_viewport=False;modifier.show_render=False
bpy.context.view_layer.update()
expressions=['eyeBlinkLeft','eyeBlinkRight','mouthSmileLeft','mouthSmileRight','jawOpen','browInnerUp']
keys=body.data.shape_keys.key_blocks;n=len(body.data.vertices);basis=np.empty(n*3,dtype=np.float32);keys[0].data.foreach_get('co',basis)
deltas={}
for name in expressions:
 if name in keys:
  a=np.empty_like(basis);keys[name].data.foreach_get('co',a);deltas[name]=a-basis;keys[name].value=0
TargetService.bake_targets(body)
base=body.shape_key_add(name='Basis');coords=np.empty(n*3,dtype=np.float32);base.data.foreach_get('co',coords)
for name,d in deltas.items():key=body.shape_key_add(name=name);key.data.foreach_set('co',coords+d);key.value=0
# Apply masks and subdivision with matching coordinates for every expression.
for m in body.modifiers:
 if m.type=='SUBSURF':m.levels=1;m.render_levels=1
ExportService.bake_modifiers_remove_helpers(body,bake_masks=True,bake_subdiv=True,remove_helpers=True,also_proxy=False)
# Visibility is explicit: strand sources are retained only in .blend, cards in GLB.
selected=[]
for o in scene.objects:
 if o.type not in ['MESH','ARMATURE','EMPTY']:continue
 if o.get('avatar_groom_role') in ['source_curves','source_guides'] or o.get('avatar_exclude_export',False) or o.get('avatar_export_exclude',False):continue
 if o.name=='Hair' and o.hide_render:continue
 if o.type=='MESH':
  # Subdivision already baked on body. Preserve needed facial shape keys.
  if o!=body and not o.data.shape_keys:
   bpy.context.view_layer.objects.active=o;o.select_set(True)
   for m in list(o.modifiers):
    if m.type in ['SUBSURF','SOLIDIFY']:
     if m.type=='SUBSURF':
      if o.name in ['Teeth','Shoes','Tongue']:
       o.modifiers.remove(m);continue
      m.levels=1
     try:bpy.ops.object.modifier_apply(modifier=m.name)
     except RuntimeError as error:raise RuntimeError(f'Cannot bake {o.name}:{m.name}: {error}')
  # Only glTF-compatible PBR maps are shipped; analytic bump is baked separately.
  for mat in o.data.materials:
   if not mat:continue
   mat.use_backface_culling=False if 'Hair' in mat.name else True
   if mat.name in ['CottonCharcoal','WoolCharcoal']:
    for shader in mat.node_tree.nodes:
     if shader.type=='BSDF_PRINCIPLED':shader.inputs['Sheen Weight'].default_value=0

 selected.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in selected:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
# Subdivision and armature deformation do not commute. Correct only the export
# bind coordinates, using the same eight influences delivered to Babylon.
cloth_report=match_cloth_surface(scene,rig,cloth_targets,max_influences=8)
(ROOT/'reports/cloth-export-correction.json').write_text(json.dumps(cloth_report,indent=2))
# Swap only delivery textures in this separate export process.
replacements={'skin-reference-clean-lids.png':'skin-color.jpg','skin-reference-soft.png':'skin-color.jpg','skin-reference-color.png':'skin-color.jpg','skin-normal.png':'skin-normal.png','skin-roughness.png':'skin-roughness.png','eye-brown-natural.png':'eye-brown-natural.png'}
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image:
   name=Path(node.image.filepath).name
   if name in replacements:
    path=ROOT/'assets/delivery'/replacements[name]
    if path.exists():
     cs=node.image.colorspace_settings.name;node.image=bpy.data.images.load(str(path),check_existing=True);node.image.colorspace_settings.name=cs
for modifier,viewport,render in armature_flags:
 modifier.show_viewport=viewport;modifier.show_render=render
bpy.context.view_layer.update()
# One deterministic head turn clip is useful for external glTF viewers.
head=rig.pose.bones['head'];head.rotation_mode='XYZ'
for frame,value in [(1,0),(31,-.18),(61,0),(91,.18),(121,0)]:
 head.rotation_euler[1]=value;head.keyframe_insert(data_path='rotation_euler',frame=frame,group='HeadTurn')
if rig.animation_data and rig.animation_data.action:rig.animation_data.action.name='HeadTurn'
scene.frame_start=1;scene.frame_end=121;scene.render.fps=30;scene.frame_set(1)
out=ROOT/'exports/avatar-uncompressed.glb';out.parent.mkdir(exist_ok=True)
kwargs={'filepath':str(out),'export_format':'GLB','use_selection':True,'export_apply':False,'export_yup':True,'export_animations':True,'export_skins':True,'export_morph':True,'export_morph_normal':True,'export_tangents':True,'export_all_influences':False,'export_influence_nb':8,'export_materials':'EXPORT','export_extras':True,'export_cameras':False,'export_lights':False}
props=bpy.ops.export_scene.gltf.get_rna_type().properties
if 'export_rest_position_armature' in props:kwargs['export_rest_position_armature']=False
bpy.ops.export_scene.gltf(**kwargs)
# Keep tangents only on materials that use them. Blender exports a zero tangent
# for a degenerate UV on the black brow mesh; unused tangent attributes are
# irrelevant to its shader and violate glTF's unit-vector requirement.
raw=out.read_bytes();json_length=struct.unpack_from('<I',raw,12)[0];document=json.loads(raw[20:20+json_length]);removed=0
for mesh in document['meshes']:
 for primitive in mesh['primitives']:
  material=document['materials'][primitive['material']]
  if 'normalTexture' not in material and 'KHR_materials_anisotropy' not in material.get('extensions',{}):
   if primitive['attributes'].pop('TANGENT',None) is not None:removed+=1
payload=json.dumps(document,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4);tail=raw[20+json_length:]
out.write_bytes(struct.pack('<III',0x46546c67,2,20+len(payload)+len(tail))+struct.pack('<II',len(payload),0x4e4f534a)+payload+tail)
print('UNUSED_TANGENT_ATTRIBUTES_REMOVED',removed,flush=True)
public=ROOT/'web/public/assets';public.mkdir(parents=True,exist_ok=True);shutil.copy2(out,public/'avatar.glb')
sha=hashlib.sha256(out.read_bytes()).hexdigest()
side={'schemaVersion':1,'modelUrl':'/assets/avatar.glb','glbSha256':sha,'metersPerUnit':1,'skinMaterials':['Skin'],'eyeMaterials':['EyeSurface'],'hairMaterials':['GroomDarkBrownCards'],'headNode':'head','hairNodes':['HairRoot.L','HairMid.L','HairTip.L','HairRoot.R','HairMid.R','HairTip.R','HairRoot.Back','HairMid.Back','HairTip.Back'],'eyeNodes':['eye.L','eye.R'],'morphTargets':{'blink':['eyeBlinkLeft','eyeBlinkRight'],'smile':['mouthSmileLeft','mouthSmileRight'],'jawOpen':['jawOpen']},'cameras':{'portrait':{'target':[0,1.435,.08],'radius':.83,'alpha':1.5707963,'beta':1.49},'full':{'target':[0,.83,0],'radius':3.25,'alpha':1.5707963,'beta':1.5},'threeQuarter':{'target':[0,1.435,.04],'radius':.86,'alpha':1.13,'beta':1.5}}}
(public/'avatar.web.json').write_text(json.dumps(side,indent=2));(ROOT/'exports/avatar.web.json').write_text(json.dumps(side,indent=2))
report={'sha256':sha,'bytes':out.stat().st_size,'expressions':list(deltas),'objects':[o.name for o in selected],'exportSettings':kwargs,'triangleCount':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in selected if o.type=='MESH')}
(ROOT/'reports/export-inventory.json').write_text(json.dumps(report,indent=2));print('EXPORT_SUCCESS',report)
