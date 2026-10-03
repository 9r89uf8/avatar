import bpy,numpy as np,json
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[2]
report={}
for name in ['AvatarBody','Eyes','Lashes']:
 o=bpy.data.objects[name]; flags=[m.show_viewport for m in o.modifiers]
 for m in o.modifiers:m.show_viewport=False
 bpy.context.view_layer.update(); ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
 v=np.array([x.co[:] for x in ev.data.vertices]);edges=np.array([e.vertices[:] for e in o.data.edges]);faces=[list(p.vertices) for p in o.data.polygons]
 normals=np.array([x.normal[:] for x in ev.data.vertices])
 np.savez_compressed(ROOT/'reports/eyelids'/(name+'.npz'),verts=v,edges=edges,normals=normals)
 for m,f in zip(o.modifiers,flags):m.show_viewport=f
 counts=defaultdict(int)
 for face in faces:
  for a,b in zip(face,face[1:]+face[:1]):counts[tuple(sorted([a,b]))]+=1
 bounds=[list(e) for e,n in counts.items() if n==1]
 report[name]={'vertices':len(v),'faces':faces,'bounds':bounds,'modifiers':[(m.name,m.type) for m in o.modifiers],'groups':[g.name for g in o.vertex_groups],'shape_keys':({k.name:k.value for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else {}),'materials':[m.name for m in o.data.materials]}
 print(name,len(v),len(bounds),'bounds',v.min(axis=0),v.max(axis=0))
(ROOT/'reports/eyelids/topology.json').write_text(json.dumps(report))
s=bpy.context.scene;s.render.resolution_x=1800;s.render.resolution_y=2200;s.render.resolution_percentage=100;s.cycles.samples=64;s.cycles.use_denoising=False;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.29;s.render.border_max_x=.71;s.render.border_min_y=.60;s.render.border_max_y=.76;s.render.filepath=str(ROOT/'renders/eyelids/neutral-before-close.png');bpy.ops.render.render(write_still=True)
