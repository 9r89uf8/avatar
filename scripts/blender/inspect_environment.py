import bpy,json,os,sys,platform,addon_utils
addon_utils.enable('cycles')
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
data={'blender':bpy.app.version_string,'build_hash':bpy.app.build_hash.decode(),'python':sys.version,'platform':platform.platform(),'engines': [x.identifier for x in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items], 'render_device':'CPU','denoising_available':False,'cpu_logical_count':os.cpu_count(),'note':'Cloud software rendering. No target-device hardware performance approval.'}
(ROOT/'reports/environment.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data,indent=2))
