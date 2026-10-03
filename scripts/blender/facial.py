"""Propagate facial units onto nearby attached brow and lash geometry."""
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

def transfer_face_targets(body,objects,names):
    # Evaluate only the shape mix, keeping original skin vertex indices.
    flags=[m.show_viewport for m in body.modifiers]
    for m in body.modifiers:m.show_viewport=False
    bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    positions=[v.co.copy() for v in ev.data.vertices]
    for m,f in zip(body.modifiers,flags):m.show_viewport=f
    group=body.vertex_groups['body'].index
    ids=[v.index for v in body.data.vertices if positions[v.index].z>1.40 and any(g.group==group for g in v.groups)]
    kd=KDTree(len(ids))
    for i in ids:kd.insert(positions[i],i)
    kd.balance();basis=body.data.shape_keys.key_blocks[0]
    for o in objects:
        if not o.data.shape_keys:o.shape_key_add(name='Basis')
        near=[]
        for v in o.data.vertices:
            candidates=kd.find_n(v.co,4);weights=[1/max(.0004,d)**3 for _,_,d in candidates];tot=sum(weights)
            near.append([(i,w/tot) for (_,i,d),w in zip(candidates,weights)])
        for name in names:
            if name not in body.data.shape_keys.key_blocks:continue
            src=body.data.shape_keys.key_blocks[name];key=o.shape_key_add(name=name);key.value=0
            for v,bs,k in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data,key.data):
                delta=Vector((0,0,0))
                for idx,w in near[v.index]:delta+=(src.data[idx].co-basis.data[idx].co)*w
                k.co=bs.co+delta
