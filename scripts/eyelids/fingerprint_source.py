import bpy,hashlib,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];result={}
for name in ['AvatarBody','Eyes','Lashes']:
 o=bpy.data.objects[name];h=hashlib.sha256()
 h.update(np.array([v.co[:] for v in o.data.vertices],np.float32).tobytes())
 h.update(np.array([i for p in o.data.polygons for i in (len(p.vertices),*p.vertices)],np.int32).tobytes())
 for uv in o.data.uv_layers:h.update(np.array([x.uv[:] for x in uv.data],np.float32).tobytes())
 keys={}
 if o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:
   h.update(k.name.encode());h.update(np.array([v.co[:] for v in k.data],np.float32).tobytes());keys[k.name]=k.value
 materials={}
 for m in o.data.materials:
  materials[m.name]=[{'type':n.type,'name':n.name,'inputs':{i.name: (list(i.default_value) if hasattr(i.default_value,'__iter__') and not isinstance(i.default_value,str) else i.default_value) for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,(float,int,str,bpy.types.bpy_prop_array))},'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m and m.use_nodes else []
 result[name]={'geometryUvKeysHash':h.hexdigest(),'shapeValues':keys,'materials':materials,'matrix':[list(r) for r in o.matrix_world]}
rig=bpy.data.objects['AvatarRig'];result['AvatarRig']={'bones':[(b.name,list(b.head_local),list(b.tail_local)) for b in rig.data.bones],'pose':[(b.name,[list(r) for r in b.matrix]) for b in rig.pose.bones]}
(ROOT/'reports/eyelids'/('fingerprint-'+Path(bpy.data.filepath).stem+'.json')).write_text(json.dumps(result,indent=2));print('FINGERPRINT_WRITTEN')
