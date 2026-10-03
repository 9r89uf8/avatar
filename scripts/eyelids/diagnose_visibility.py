import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];body=bpy.data.objects['AvatarBody'];cam=bpy.context.scene.camera
body.modifiers['PortraitSubdivision'].levels=2;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();bv=BVHTree.FromObject(body,dg);o=bpy.data.objects['LidCandidate_Lashes'];ev=o.evaluated_get(dg);v=np.array([x.co[:] for x in ev.data.vertices]);out={}
for label,indices in [('upper',list(range(106))+list(range(144,250))),('lower',list(range(106,144))+list(range(250,288)))]:
 for ring in [2,5]:
  visible=0;gaps=[]
  for i in indices:
   pt=Vector(v[i*24+ring*4:i*24+ring*4+4].mean(axis=0));d=(pt-cam.location);L=d.length;d.normalize();hit,normal,index,dist=bv.ray_cast(cam.location,d)
   if dist is None or dist>L:visible+=1
   elif dist:gaps.append((L-dist)*1000)
  out[label+str(ring)]={'count':len(indices),'visible':visible,'occludedDepthMm':gaps}
print(json.dumps(out,indent=2));(ROOT/'reports/eyelids/visibility-v2.json').write_text(json.dumps(out,indent=2))
print('FLAGS',o.hide_render,o.hide_get(),o.visible_camera,o.parent.name)
