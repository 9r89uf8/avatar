"""Preserve the posed cloth surface across noncommuting armature/subdivision bake.

The correction is export-only. It inverse-skins the desired evaluated surface
back into the existing rig's bind coordinates, so portable linear skinning
reproduces the source pose without changing editable source geometry.
"""
import bpy
from mathutils import Matrix

def capture_cloth_surface(scene, names=('CharcoalTee','CollarRibbing')):
    result={}
    for name in names:
        ob=scene.objects.get(name)
        if not ob:continue
        for mod in ob.modifiers:
            if mod.type=='SUBSURF':mod.levels=1
        bpy.context.view_layer.update()
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        result[name]=[v.co.copy() for v in mesh.vertices]
        ev.to_mesh_clear()
    return result

def match_cloth_surface(scene,rig,targets,max_influences=8):
    report={}
    bones={b.name:b for b in rig.pose.bones if b.bone.use_deform}
    bm={name:b.matrix@b.bone.matrix_local.inverted() for name,b in bones.items()}
    for name,target in targets.items():
        ob=scene.objects.get(name)
        if len(ob.data.vertices)!=len(target):raise ValueError(f'Cloth topology mismatch {name}: {len(ob.data.vertices)} != {len(target)}')
        mat=rig.matrix_world.inverted()@ob.matrix_world;imat=mat.inverted();deltas=[]
        for v,wanted in zip(ob.data.vertices,target):
            influences=[(bm[ob.vertex_groups[g.group].name],g.weight) for g in v.groups if ob.vertex_groups[g.group].name in bm and g.weight>0]
            influences=sorted(influences,key=lambda pair:pair[1],reverse=True)[:max_influences]
            total=sum(w for _,w in influences)
            if not total:continue
            blend=Matrix(tuple(tuple(sum(m[r][c]*w/total for m,w in influences) for c in range(4)) for r in range(4)))
            corrected=imat@(blend.inverted()@(mat@wanted))
            deltas.append((corrected-v.co).length);v.co=corrected
        ob.data.update();report[name]={'vertices':len(target),'maxBindCorrectionMeters':max(deltas),'meanBindCorrectionMeters':sum(deltas)/len(deltas)}
    return report
