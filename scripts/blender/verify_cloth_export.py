"""Compare evaluated source garment vertices with a clean GLB re-import.

Run Blender with avatar-master.blend loaded. It replaces this process's scene,
never saves the editable file, and exits nonzero if surface parity is lost.
"""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,kdtree
ROOT=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
glb=Path(args[0]) if args else ROOT/'exports/avatar-uncompressed.glb'
source={}
for name in ['CharcoalTee','CollarRibbing']:
    ob=bpy.data.objects.get(name)
    if ob is None:raise RuntimeError(f'Source missing {name}')
    for m in ob.modifiers:
        if m.type=='SUBSURF':m.levels=1
    bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    source[name]=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(glb))
report={'glbSha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'method':'Nearest source vertex after same delivery subdivision. GLB UV/normal vertex splits are expected.','toleranceMeters':.00005,'objects':{},'passed':True}
for name,points in source.items():
    ob=bpy.data.objects.get(name)
    if ob is None:raise RuntimeError(f'GLB missing {name}')
    kd=kdtree.KDTree(len(points))
    for i,p in enumerate(points):kd.insert(p,i)
    kd.balance();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();distance=[kd.find(ev.matrix_world@v.co)[2] for v in me.vertices]
    passed=max(distance)<=report['toleranceMeters']
    report['objects'][name]={'sourceVertices':len(points),'glbVertices':len(distance),'maxDistanceMeters':max(distance),'meanDistanceMeters':sum(distance)/len(distance),'passed':passed}
    report['passed'] &= passed;ev.to_mesh_clear()
(ROOT/'reports/cloth-export-parity.json').write_text(json.dumps(report,indent=2));print('CLOTH_EXPORT_PARITY',json.dumps(report),flush=True)
if not report['passed']:raise RuntimeError('GLB cloth differs from evaluated source beyond tolerance')
