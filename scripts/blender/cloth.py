"""Small, physically scaled fabric surface and seam refinements."""
import bpy,math
from mathutils import Vector

def refine_clothing(shirt,rig):
    # Low-amplitude cloth relief follows the jersey's gravity and shoulder tension.
    for v in shirt.data.vertices:
        x,y,z=v.co
        # Long, shallow hanging folds, quieter at the neckline.
        w=max(0,min(1,(1.29-z)/.18))
        front=max(0,min(1,(-y-.04)/.06))
        amp=.0019*w*front
        v.co.y+=amp*(math.sin(x*100+z*14)+.45*math.sin(x*163-z*17))
    mat=shirt.data.materials[0];p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n=mat.node_tree.nodes;lk=mat.node_tree.links
    co=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2100;noise.inputs['Detail'].default_value=1
    lk.new(co.outputs['Object'],noise.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.000085;bump.inputs['Strength'].default_value=.26;lk.new(noise.outputs['Fac'],bump.inputs['Height']);lk.new(bump.outputs['Normal'],p.inputs['Normal'])
    p.inputs['Sheen Weight'].default_value=.13
    # Preserve garment thickness and hem silhouette without swelling the whole mesh.
    solid=shirt.modifiers.new('CottonThickness','SOLIDIFY');solid.thickness=.0012;solid.offset=-.5
    # Boundary edge loop at neckline becomes a separate narrow raised ribbing seam.
    counts={}
    for face in shirt.data.polygons:
        vs=list(face.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):
            k=tuple(sorted((a,b)));counts[k]=counts.get(k,0)+1
    edges=[e for e,c in counts.items() if c==1 and all(shirt.data.vertices[i].co.z>1.24 and abs(shirt.data.vertices[i].co.x)<.115 for i in e)]
    adj={}
    for a,b in edges:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
    if len(adj)<10:return []
    start=min(adj);chain=[start];prev=None;cur=start
    while True:
        candidates=[x for x in adj[cur] if x!=prev]
        if not candidates:break
        nxt=candidates[0]
        if nxt==start:break
        chain.append(nxt);prev,cur=cur,nxt
        if len(chain)>len(adj)+1:break
    if len(chain)<10:return []
    verts=[];faces=[];R=8
    for k,i in enumerate(chain):
        c=shirt.data.vertices[i].co.copy();pr=shirt.data.vertices[chain[k-1]].co;nx=shirt.data.vertices[chain[(k+1)%len(chain)]].co
        tangent=(nx-pr).normalized();normal=shirt.data.vertices[i].normal.normalized();side=tangent.cross(normal).normalized()
        for j in range(R):
            a=j/R*math.tau;v=c+normal*(.0017+.0015*math.cos(a))+side*(.0032*math.sin(a));verts.append(v)
    for k in range(len(chain)):
        for j in range(R):faces.append((k*R+j,k*R+(j+1)%R,((k+1)%len(chain))*R+(j+1)%R,((k+1)%len(chain))*R+j))
    mesh=bpy.data.meshes.new('CollarRibbing');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('CollarRibbing',mesh);bpy.context.scene.collection.objects.link(o);o.data.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=True
    # Seam follows the same nearby garment weights, including the neck and shoulder rig.
    for vg in shirt.vertex_groups:o.vertex_groups.new(name=vg.name)
    for k,i in enumerate(chain):
        for gw in shirt.data.vertices[i].groups:o.vertex_groups[gw.group].add(list(range(k*R,(k+1)*R)),gw.weight,'REPLACE')
    sub=o.modifiers.new('CollarSmooth','SUBSURF');sub.levels=1;sub.render_levels=2
    arm=o.modifiers.new('Armature','ARMATURE');arm.object=rig;o.parent=rig
    return [o]
