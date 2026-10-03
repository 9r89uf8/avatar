import bpy,sys,json,struct,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
VERSION=Path(bpy.data.filepath).stem.split('-')[-1]
s=bpy.context.scene;rig=bpy.data.objects['AvatarRig'];obs=[bpy.data.objects[n] for n in ['LidCandidate_Wetline','LidCandidate_Lashes']]
report={'source':bpy.data.filepath,'objects':{},'poses':{}}
for o in obs:
 v=np.array([x.co[:] for x in o.data.vertices]);tris=[];o.data.calc_loop_triangles()
 for t in o.data.loop_triangles:tris.append(t.vertices[:])
 t=np.array(tris);area=np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)*.5
 assert np.isfinite(v).all() and area.min()>1e-14
 weights=[sum(g.weight for g in x.groups) for x in o.data.vertices]
 assert max(abs(x-1) for x in weights)<1e-6
 report['objects'][o.name]={'vertices':len(v),'triangles':len(t),'minimumTriangleAreaM2':float(area.min()),'zeroAreaTriangles':int((area<=1e-14).sum()),'shapeKeys':[k.name for k in o.data.shape_keys.key_blocks],'allWeightsNormalized':True,'armature':o.modifiers[0].object.name}
for label,blink,yaw,gaze in [('neutral',0,0,0),('blink',1,0,0),('blink-turn',1,.35,.12),('gaze',0,0,.15)]:
 for o in s.objects:
  if o.type=='MESH' and o.data.shape_keys:
   for name in ['eyeBlinkLeft','eyeBlinkRight']:
    if name in o.data.shape_keys.key_blocks:o.data.shape_keys.key_blocks[name].value=blink
 head=rig.pose.bones['head'];head.rotation_mode='XYZ';head.rotation_euler[1]=yaw
 for name in ['eye.L','eye.R']:
  rig.pose.bones[name].rotation_mode='XYZ';rig.pose.bones[name].rotation_euler[2]=gaze
 bpy.context.view_layer.update();row={}
 for o in obs:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());v=np.array([x.co[:] for x in ev.data.vertices]);assert np.isfinite(v).all();row[o.name]={'vertices':len(v),'min':v.min(axis=0).tolist(),'max':v.max(axis=0).tolist()}
 report['poses'][label]=row
# Portable isolated accessory export, leaving production GLB and viewer untouched.
for o in s.objects:
 if o.type=='MESH' and o.data.shape_keys:
  for name in ['eyeBlinkLeft','eyeBlinkRight']:
   if name in o.data.shape_keys.key_blocks:o.data.shape_keys.key_blocks[name].value=0
head.rotation_euler[1]=0
for name in ['eye.L','eye.R']:rig.pose.bones[name].rotation_euler[2]=0
bpy.ops.object.select_all(action='DESELECT')
for o in obs+[rig]:o.hide_set(False);o.select_set(True)
out=ROOT/'reports/eyelids'/('eyelid-accessory-'+VERSION+'.glb')
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_animations=False,export_skins=True,export_morph=True,export_materials='EXPORT',export_extras=True,export_cameras=False,export_lights=False)
raw=out.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);report['glTF']={'bytes':len(raw),'meshes':[{'name':m.get('name'),'targetNames':m.get('extras',{}).get('targetNames'),'morphCounts':[len(p.get('targets',[])) for p in m['primitives']]} for m in doc['meshes']],'materials':[m['name'] for m in doc['materials']],'extensionsUsed':doc.get('extensionsUsed',[]),'skins':len(doc.get('skins',[]))}
(ROOT/'reports/eyelids'/('validation-'+VERSION+'.json')).write_text(json.dumps(report,indent=2));print('LID_VALIDATION',report['glTF'])
