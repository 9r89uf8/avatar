import bpy,json
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];s=bpy.context.scene
calibration_path=ROOT/'config/reference-camera.json'
if calibration_path.exists():
 calibration=json.loads(calibration_path.read_text());s.camera.matrix_world=Matrix(calibration['matrix_world']);s.camera.data.lens=calibration['lens'];s.camera.data.sensor_width=calibration['sensor_width'];s.render.resolution_x=900;s.render.resolution_y=1100
o=bpy.data.objects['AvatarBody'];b=o.vertex_groups['body'].index
# Evaluate shape-key mix without topology/rig modifiers to preserve original indices.
show=[m.show_viewport for m in o.modifiers]
for m in o.modifiers:m.show_viewport=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);verts=[]
for i,v in enumerate(ev.data.vertices):
 if not any(g.group==b for g in o.data.vertices[i].groups):continue
 co=o.matrix_world@v.co;p=world_to_camera_view(s,s.camera,co)
 if co.z>1.33:verts.append({'index':i,'co':list(co),'xy':[p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y],'depth':p.z,'normal':list(v.normal)})
for m,x in zip(o.modifiers,show):m.show_viewport=x
uv=o.data.uv_layers.active.data
triangles=[]
o.data.calc_loop_triangles()
for t in o.data.loop_triangles:
 if all(o.data.vertices[i].co.z>1.32 for i in t.vertices):
  triangles.append({'indices':list(t.vertices),'uv':[list(uv[k].uv) for k in t.loops]})
out={'triangles':triangles,'width':s.render.resolution_x,'height':s.render.resolution_y,'vertices':verts,'camera':{'matrix_world':[list(r) for r in s.camera.matrix_world],'lens':s.camera.data.lens,'sensor_width':s.camera.data.sensor_width},'root':str(ROOT),'model_scale':.1}
(ROOT/'reports/face-projection.json').write_text(json.dumps(out))
print('WROTE',len(verts))
