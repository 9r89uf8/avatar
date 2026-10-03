"""Read-only source integrity report. Run in a fresh Blender process."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
missing=[];images=[]
for im in bpy.data.images:
 if im.source!='FILE':continue
 p=Path(bpy.path.abspath(im.filepath));packed=bool(im.packed_file or im.packed_files)
 if not packed and not p.exists():missing.append(str(p))
 images.append({'name':im.name,'size':list(im.size),'colorSpace':im.colorspace_settings.name,'packed':packed})
objects=[]
for o in bpy.context.scene.objects:
 row={'name':o.name,'type':o.type,'dimensions':list(o.dimensions),'parent':o.parent.name if o.parent else None}
 if o.type=='MESH':row.update({'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'uvMaps':[u.name for u in o.data.uv_layers],'materials':[m.name for m in o.data.materials],'morphs':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []})
 if o.type=='ARMATURE':row['bones']=[b.name for b in o.data.bones]
 objects.append(row)
report={'source':bpy.data.filepath,'sourceSha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'missingFiles':missing,'images':images,'objects':objects,'renderEngine':bpy.context.scene.render.engine,'viewTransform':bpy.context.scene.view_settings.view_transform}
(ROOT/'reports/source-reopened.json').write_text(json.dumps(report,indent=2))
print('SOURCE_REOPENED',len(objects),'objects',len(images),'images',len(missing),'missing')
if missing:raise RuntimeError('Missing source dependencies')
