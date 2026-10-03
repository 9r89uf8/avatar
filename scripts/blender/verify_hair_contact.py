import bpy,json,math,sys,hashlib,itertools
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/blender'))
from groom import _objects_bvh
s=bpy.context.scene;r=bpy.data.objects['AvatarRig'];human=bpy.data.objects['AvatarBody']
colliders=[human]+[o for o in s.objects if o.name in ('CharcoalTee','CollarRibbing') and o.type=='MESH']
cards=[o for o in s.objects if o.get('avatar_groom_role')=='web_cards']
report={'sourceSha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scope':'Front-contact card vertices below chest threshold; not an exhaustive whole-hair collision proof. Includes UI yaw plus idle yaw/pitch/roll envelope.','scenarios':[],'groom_inventory':json.loads(s['groom_inventory'])}
scenarios=[(0,0,0,0),(25,0,0,0),(-25,0,0,0)]
limit=25+math.degrees(.015)
scenarios+=list(itertools.product([-limit,limit],[-.065,.065],[-.006,.006],[-.004,.004]))
for yaw,offset,pitch,roll in scenarios:
 for bone in r.pose.bones:
  if bone.name.startswith(('HairRoot.','HairMid.','HairTip.')):
   strength=.22 if 'Root' in bone.name else .66 if 'Mid' in bone.name else 1
   side=-1 if bone.name.endswith('.R') else 1
   bone.rotation_mode='XYZ';bone.rotation_euler=(offset*strength*.28,offset*strength*.35,offset*strength*side)
 r.pose.bones['head'].rotation_mode='XYZ';r.pose.bones['head'].rotation_euler=(pitch,math.radians(yaw),roll);bpy.context.view_layer.update()
 tree=_objects_bvh(colliders);deps=bpy.context.evaluated_depsgraph_get();clearances=[];checks=0;negative=[]
 for ob in cards:
  chest=ob.vertex_groups.get('spine01')
  if not chest:continue
  ev=ob.evaluated_get(deps);mesh=ev.to_mesh()
  for v in ob.data.vertices:
   if v.co.z>=1.36 or not any(g.group==chest.index and g.weight>0 for g in v.groups):continue
   point=ob.matrix_world@mesh.vertices[v.index].co
   hit,n,i,d=tree.ray_cast(Vector((point.x,-.45,point.z)),Vector((0,1,0)),.85)
   if hit:
    clearance=hit.y-point.y;clearances.append(clearance);checks+=1
    if clearance<0:negative.append((ob.name,v.index,float(clearance),list(point)))
  ev.to_mesh_clear()
 report['scenarios'].append({'head_yaw_degrees':yaw,'spring_offset_radians':offset,'idle_pitch_radians':pitch,'idle_roll_radians':roll,'chest_contact_vertices_checked':checks,'minimum_front_clearance_m':min(clearances) if clearances else None,'penetrating_vertices':len(negative),'examples':negative[:8]})
r.pose.bones['head'].rotation_euler=(0,0,0);bpy.context.view_layer.update()
report['weight_sum_error_max']=max(abs(1-sum(g.weight for g in v.groups)) for ob in cards for v in ob.data.vertices)
(ROOT/'reports/groom/runtime-hair-contact.json').write_text(json.dumps(report,indent=2))

print(json.dumps(report,indent=2))
if any(x['penetrating_vertices'] for x in report['scenarios']):raise RuntimeError('Hair contact validation failed')
