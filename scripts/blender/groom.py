"""Deterministic parted dark-brown groom with editable strand source and skinned glTF cards.

Ownership: generated project asset; no third-party texture pixels. Metres, Blender Z-up.
Call build_groom(human, rig, existing_hair). Native hair curves receive skinned source-mesh edges through Geometry Nodes
*after* armature deformation. Browser cards follow the
same guides and exact root-preserving weights. Filter avatar_groom_role on export.
"""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'docs/brief.md').is_file() and (p/'scripts/blender').is_dir())
OUT=ROOT/'assets/groom'
SEED=42117
HEAD='head'
CHAINS={k:[f'HairRoot.{k}',f'HairMid.{k}',f'HairTip.{k}'] for k in ['L','R','Back']}

def smooth(x):
 x=max(0.,min(1.,x)); return x*x*(3-2*x)

def _catmull(points, count):
 pp=[Vector(points[0])]+[Vector(p) for p in points]+[Vector(points[-1])]
 out=[]
 for i in range(count):
  v=i/(count-1)*(len(points)-1);k=min(int(v),len(points)-2);t=v-k
  a,b,c,d=pp[k:k+4]
  out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 return out

def _skin(ob,rig,side,positions):
 names=[HEAD]+CHAINS[side]
 groups={n:ob.vertex_groups.new(name=n) for n in names}
 if 'spine01' in rig.data.bones:groups['spine01']=ob.vertex_groups.new(name='spine01')
 buckets={}
 for i,p in enumerate(positions):
  z=p[2]
  if z>=1.475:w=[(HEAD,1.)]
  elif z>=1.35:
   t=smooth((1.475-z)/.125);w=[(HEAD,1-t),(names[1],t)]
  elif z>=1.17:
   t=smooth((1.35-z)/.18);w=[(names[1],1-t),(names[2],t)]
  else:
   t=smooth((1.17-z)/.17);w=[(names[2],1-t),(names[3],t)]
  # The few front locks rest on clothing: chest contact supplies friction,
  # while the scalp and upper free span keep their head-driven motion.
  if side!='Back' and 'spine01' in groups and p[1]<-.031 and z<1.400:
   contact=.99*smooth((1.40-z)/.055)
   w=[(name,weight*(1-contact)) for name,weight in w]+[('spine01',contact)]
  quant=[round(weight*256) for name,weight in w]
  quant[max(range(len(w)),key=lambda k:w[k][1])]+=256-sum(quant)
  for (name,weight),q in zip(w,quant):
   if q:buckets.setdefault((name,q),[]).append(i)
 for (name,q),indices in buckets.items():groups[name].add(indices,q/256.,'REPLACE')
 arm=ob.modifiers.new('HeadDrivenHairSkin','ARMATURE');arm.object=rig
 ob.parent=rig;ob.matrix_parent_inverse=rig.matrix_world.inverted()


def _bones(rig):
 if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.object.mode_set(mode='EDIT')
 for side,x,y in [('L',.084,.025),('R',-.084,.025),('Back',0,.10)]:
  parent=rig.data.edit_bones[HEAD]
  for i,name in enumerate(CHAINS[side]):
   b=rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name)
   b.head=(x,y,1.46-i*.19);b.tail=(x,y,1.27-i*.19);b.parent=parent;b.use_connect=False;parent=b
 bpy.ops.object.mode_set(mode='OBJECT')
 for chain in CHAINS.values():
  for name in chain:
   b=rig.pose.bones[name];b.rotation_mode='XYZ';b['secondary_motion']=True
   b['limit_degrees']=9 if 'Root' in name else 14


def _material_cards():
 # Isolated candidate reuses the approved packed texture and PBR material.
 existing=bpy.data.materials.get('GroomDarkBrownCards')
 if existing:return existing
 OUT.mkdir(parents=True,exist_ok=True)
 width,height=512,1024
 rng=np.random.default_rng(SEED)
 x=np.arange(width)[None,:];t=np.arange(height)[:,None]/(height-1)
 alpha=np.zeros((height,width),np.float32);color=np.zeros((height,width,3),np.float32)
 centers=np.linspace(5,width-6,54)+rng.uniform(-3,3,54)
 for j,c in enumerate(centers):
  drift=rng.uniform(.4,3)*np.sin(t*rng.uniform(3,10)+rng.uniform(0,6))
  w=rng.uniform(2.4,4.0)*(1-.78*t**8)
  stripe=np.exp(-((x-c-drift)/w)**4)
  # Thousands of resolved fibers, tapered and gently separated at their tips.
  stop=rng.uniform(.88,1.05);fade=np.clip((stop-t)*50,0,1)
  a=stripe*fade*rng.uniform(.78,1.)
  shade=rng.uniform(.72,1.3)*(1+.05*np.sin(t*rng.uniform(9,19)+j))
  cbase=np.array([.205,.135,.086],np.float32)
  for k in range(3):color[:,:,k]+=a*shade*cbase[k]
  alpha+=a
 color/=np.maximum(alpha[:,:,None],.00001);alpha=np.clip(alpha,0,1)
 # Transparent borders and randomized root coverage remove ribbon edges.
 alpha[:8]*=np.linspace(.35,1,8)[:,None]
 rgba=np.concatenate([np.clip(color,0,1),alpha[:,:,None]],axis=2).astype(np.float32)
 # UV V=1 roots, V=0 tips; texture rows bottom to top in Blender.
 rgba=rgba[::-1].copy()
 im=bpy.data.images.new('GroomFiberAtlas',width=width,height=height,alpha=True)
 im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/'groom_fibers_rgba.png');im.file_format='PNG';im.save();im.pack()
 mat=bpy.data.materials.new('GroomDarkBrownCards');mat.use_nodes=True
 mat.diffuse_color=(.035,.016,.0065,1);mat.use_backface_culling=False
 if hasattr(mat,'surface_render_method'):mat.surface_render_method='DITHERED'
 nodes=mat.node_tree.nodes;links=mat.node_tree.links;p=nodes.get('Principled BSDF')
 p.inputs['Roughness'].default_value=.52;p.inputs['Specular IOR Level'].default_value=.23
 p.inputs['Anisotropic'].default_value=.65
 tex=nodes.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Linear';tex.extension='CLIP'
 links.new(tex.outputs['Color'],p.inputs['Base Color']);links.new(tex.outputs['Alpha'],p.inputs['Alpha'])
 return mat


def _material_strands():
 mat=bpy.data.materials.new('GroomNaturalBrownFibers');mat.use_nodes=True
 n=mat.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');hair=n.new('ShaderNodeBsdfHairPrincipled')
 hair.parametrization='COLOR';hair.inputs['Color'].default_value=(.008,.0055,.0038,1)
 hair.inputs['Roughness'].default_value=.31
 if 'Radial Roughness' in hair.inputs:hair.inputs['Radial Roughness'].default_value=.39
 if 'Random Color' in hair.inputs:hair.inputs['Random Color'].default_value=.11
 if 'Random Roughness' in hair.inputs:hair.inputs['Random Roughness'].default_value=.12
 info=n.new('ShaderNodeHairInfo');ramp=n.new('ShaderNodeValToRGB')
 ramp.color_ramp.elements[0].position=.12;ramp.color_ramp.elements[0].color=(.0035,.002,.0012,1)
 ramp.color_ramp.elements[1].position=.92;ramp.color_ramp.elements[1].color=(.028,.013,.005,1)
 ramp.color_ramp.elements.new(.5).color=(.011,.006,.0028,1)
 mat.node_tree.links.new(info.outputs['Random'],ramp.inputs['Fac']);mat.node_tree.links.new(ramp.outputs['Color'],hair.inputs['Color'])
 mat.node_tree.links.new(hair.outputs[0],out.inputs['Surface']);return mat


def _curve_nodes(ob,mat,points_object):
 ng=bpy.data.node_groups.new('GroomEdgesToTrueHairCurves','GeometryNodeTree')
 ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
 ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
 n=ng.nodes;l=ng.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');mc=n.new('GeometryNodeMeshToCurve')
 radius=n.new('GeometryNodeSetCurveRadius');att=n.new('GeometryNodeInputNamedAttribute');att.data_type='FLOAT';att.inputs['Name'].default_value='strand_radius'
 material=n.new('GeometryNodeSetMaterial');material.inputs['Material'].default_value=mat
 info=n.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=points_object;info.transform_space='RELATIVE'
 l.new(info.outputs['Geometry'],mc.inputs['Mesh']);l.new(mc.outputs['Curve'],radius.inputs['Curve']);l.new(att.outputs['Attribute'],radius.inputs['Radius']);l.new(radius.outputs['Curve'],material.inputs['Geometry']);l.new(material.outputs['Geometry'],out.inputs['Geometry'])
 mod=ob.modifiers.new('ActualTaperedRenderCurves','NODES');mod.node_group=ng


def _objects_bvh(objects):
 deps=bpy.context.evaluated_depsgraph_get();vs=[];faces=[]
 for obj in objects:
  ev=obj.evaluated_get(deps);mesh=ev.to_mesh();start=len(vs)
  vs.extend(obj.matrix_world@v.co for v in mesh.vertices)
  faces.extend(tuple(start+i for i in p.vertices) for p in mesh.polygons)
  ev.to_mesh_clear()
 return BVHTree.FromPolygons(vs,faces)


def _scalp_bvh(human):
 return _objects_bvh([human])


def _front_lock_spec(label,layer,index):
 if label=='L':
  for lo,hi,kind in [(9,12,0),(21,24,1),(31,33,2)]:
   if lo<=index<=hi:return lo,hi,kind
 elif label=='R' and layer<2 and 11<=index<=14:return 11,14,3
 return None


def _base_guide_data(human):
 rng=random.Random(SEED);tree=_scalp_bvh(human)
 collision=_objects_bvh([human]+[o for o in bpy.context.scene.objects if o.name in ('CharcoalTee','CollarRibbing') and o.type=='MESH'])
 C=Vector((0,-.035,1.50));all_guides={k:[] for k in CHAINS}
 def top(x,y):
  loc,normal,idx,dist=tree.ray_cast(Vector((x,y,1.75)),Vector((0,0,-1)),.3)
  return loc.z if loc else 1.59
 def clear(pt,clearance):
  p=Vector(pt);d=(p-C).normalized();loc,n,idx,dist=tree.ray_cast(C,d,.25)
  if loc:
   radius=max((p-C).length,(loc-C).length+clearance);p=C+d*radius
  return p
 for side,label in [(-1,'R'),(1,'L')]:
  for layer in range(3):
   for j in range(138):
    q=(j+rng.uniform(-.48,.48))/137.;root_y=-.127+q*.169
    part=.0075+.0017*math.sin(q*9+.35)+.00065*math.sin(q*31);gap=.00028+.00028*(.5+.5*math.sin(q*23+.6))
    root_x=part+side*(gap+layer*.00018)+rng.uniform(-.00022,.00022)
    root_z=top(root_x,root_y)+.001+layer*.0007
    end_y=-.025+q*.080;end_x=side*(.080+.0035*layer+.008*math.sin(q*math.pi))
    pts=[]
    for k in range(10):
     u=k/9.;x=root_x*(1-smooth(u))+end_x*math.sin(u*math.pi/2)
     y=root_y+(end_y-root_y)*u**2.35+.0022*math.sin(q*24+layer*.7)*math.sin(u*math.pi)
     z=root_z-(root_z-1.478)*(1-math.cos(u*math.pi/2))+.0012*math.sin(q*21+.7)*math.sin(u*math.pi)
     p=clear((x,y,z),.0020+layer*.0027+.0042*math.sin(u*math.pi))
     normal=(p-C).normalized();clump=(.0018*(.5+.5*math.sin(q*36+layer*.6))+.0012*(.5+.5*math.sin(q*83+.7)))*math.sin(u*math.pi)**2
     p+=normal*clump;pts.append(p)
    # Long hanging lengths are behind the ears and garment, with restrained bend.
    phase=rng.uniform(0,6.28);length=rng.uniform(.445,.600)
    if q<.21 and rng.random()<.24:length=rng.uniform(.23,.37)
    for u in [.20,.42,.67,.84,1.]:
     z=1.478-length*u
     x=end_x+side*(.014*math.sin(u*math.pi*.9)+.016*u)+side*.008*math.sin(u*6.3+q*8+.3*side)*math.sin(math.pi*u**.85)+.003*math.sin(u*12+q*25)*u
     y=end_y+.018*math.sin(u*math.pi/2)+.040*smooth((u-.12)/.8)+.0065*math.sin(u*4.7+q*11+side)*math.sin(u*math.pi)
     pts.append(Vector((x,y,z)))
    lock=_front_lock_spec(label,layer,j)
    if lock:
     lo,hi,kind=lock;f=(j-lo)/max(1,hi-lo)
     shoulder=[.100+.009*f,.118+.009*f,.093+.008*f,.108+.008*f][kind]
     tip_x=[.078+.009*f,.095+.008*f,.103+.006*f,.088+.007*f][kind]
     tip_z=[1.205+.022*math.sin(f*math.pi),1.175+.018*math.sin(f*5),1.245+.014*math.sin(f*4),1.245+.018*math.sin(f*4)][kind]
     tip_z+=rng.uniform(-.007,.007)+(layer-1)*.008
     shoulder=side*(shoulder+layer*.002);tip_x=side*(tip_x+layer*.0014)
     pts=pts[:10]
     for u in [.12,.26,.42,.60,.78,1.]:
      z=1.478+(tip_z-1.478)*u
      x=end_x+(shoulder-end_x)*smooth(u/.43)+(tip_x-shoulder)*smooth((u-.42)/.58)
      x+=side*.0018*math.sin(u*5+kind)*math.sin(math.pi*u)
      y=end_y-.029*smooth((1.46-z)/.15)
      pts.append(Vector((x,y,z)))
     path=_catmull(pts,40)
     for point in path:
      if point.z<1.468:
       hit,nn,ii,dd=collision.ray_cast(Vector((point.x,-.45,point.z)),Vector((0,1,0)),.85)
       if hit:
        front=hit.y-(.007+layer*.0007)
        drape=smooth((1.365-point.z)/.045)
        point.y=min(point.y,front)*(1-drape)+front*drape
    else:path=_catmull(pts,36)
    all_guides[label].append((path,rng.uniform(.0022,.0035)*(.62 if lock else 1.),rng.random()))
 # A separate posterior cascade fills the occiput without a cap or forehead sheet.
 for layer in range(3):
  for j in range(115):
   a=(j+rng.uniform(-.3,.3))/114.;x=-.053+.106*a
   # Posterior infill is rooted under the side groom at the occiput. Starting it
   # on the crown makes a detached folded overlap in profile, so keep its upper
   # points slightly buried and let fibers emerge naturally down the nape.
   z0=1.535+.021*math.exp(-(x/.025)**2)
   hit,nn,ii,dd=tree.ray_cast(Vector((x,.2,z0)),Vector((0,-1,0)),.35)
   y=(hit.y if hit else .033)+.0014+layer*.0007
   pts=[(x,y,z0),(x*1.2,.043+layer*.0015,1.50),(x*1.5,.056+layer*.002,1.455),(x*1.9,.070+layer*.002,1.39),(x*2.2,.090+layer*.002,1.28),(x*2.43,.102, rng.uniform(.90,1.01))]
   pts=[Vector(p) for p in pts]
   for k,p in enumerate(pts):
    t=k/(len(pts)-1);p.x+=.007*math.sin(t*5+a*11)*math.sin(t*math.pi);p.y+=.004*math.sin(t*7+a*9)*math.sin(t*math.pi)
    edge=smooth((abs(a-.5)-.38)/.12);p.x+=edge*.006*math.sin(t*5+a*12+layer)*math.sin(t*math.pi)
   back_path=_catmull(pts,36)
   # Keep the whole interpolated root section outside the real occiput, not
   # just its end points: skull convexity otherwise hides a central patch.
   for point in back_path:
    if point.z>1.445:
     hit,nn,ii,dd=tree.ray_cast(Vector((point.x,.2,point.z)),Vector((0,-1,0)),.35)
     if hit:point.y=max(point.y,hit.y+.0024+layer*.0012)
   all_guides['Back'].append((back_path,rng.uniform(.0025,.0038),rng.random()))
 # Short flyaway/baby-hair guides soften the temporal boundary without a sheet.
 for side,label in [(-1,'R'),(1,'L')]:
  front=all_guides[label][0][0]
  for j in range(48):
   u=rng.uniform(6.,22.);k=min(int(u),len(front)-2);t=u-k
   root=front[k].lerp(front[k+1],t)+Vector((0,-.0008,0))
   tangent=(front[min(k+2,len(front)-1)]-front[max(0,k-1)]).normalized()
   length=rng.uniform(.006,.016);normal=(root-C).normalized();points=[]
   for n in range(12):
    t=n/11.;points.append(root+tangent*(length*t)+normal*(.0011*math.sin(t*math.pi))+Vector((0,-.0015*t, -.002*t*t)))
   all_guides[label].append((_catmull(points,16),rng.uniform(.00025,.00055),rng.random()))
  # A few silhouette strands have a larger, coherent offset than the dense mass.
  # They are shared with the browser, so this is real geometry rather than a render trick.
  main_paths=all_guides[label][:414]
  for j in range(32):
   base=main_paths[rng.randrange(276,414)][0];points=[];phase=rng.uniform(0,6.28)
   amplitude=rng.uniform(.003,.0075)*(1.15 if side<0 else .90)
   for k,p in enumerate(base):
    t=k/(len(base)-1);n=(p-C).normalized() if t<.60 else Vector((side*.85,.4,0)).normalized()
    offset=amplitude*math.sin(math.pi*t)**1.2*(.65+.35*math.sin(t*7+phase))
    points.append(p+n*offset+Vector((side*.0015*math.sin(t*8+phase)*math.sin(math.pi*t),0,0)))
   all_guides[label].append((points,rng.uniform(.00018,.00038),rng.random()))
 return all_guides


def _guide_data(human):
 # Author the root patches while retaining the reviewed downstream groom
 # verbatim. This prevents a local part correction from re-cutting the drape.
 guides=_base_guide_data(human);tree=_scalp_bvh(human);C=Vector((0,-.035,1.50))
 for label in ['L','R']:
  old_paths=[entry[0] for entry in guides[label][:414]]
  for j in range(414):
   original,width,seed=guides[label][j];layer=j//138
   rng=random.Random(SEED+30000+j*97+(0 if label=='L' else 1000))
   index=rng.uniform(0,.10) if layer==0 else rng.uniform(.04,.20) if layer==1 else rng.uniform(.65,2.5)
   k=int(index);root=original[k].lerp(original[k+1],index-k)
   hit,normal,ii,dd=tree.ray_cast(C,(root-C).normalized(),.25)
   if not hit:continue
   root=hit+normal*.00010
   tangent=(original[k+1]-original[k])+Vector((0,rng.uniform(-.001,.003),0))
   tangent-=normal*tangent.dot(normal);tangent.normalize()
   end=original[6];distance=(end-root).length
   p1=root+tangent*min(.008,distance*.3)+normal*.0006
   p2=end-(original[7]-original[5]).normalized()*min(.009,distance*.35)
   dense=[]
   for i in range(120):
    t=i/119.;dense.append(root*(1-t)**3+p1*(3*(1-t)**2*t)+p2*(3*(1-t)*t*t)+end*t**3)
   lengths=[0.]
   for a,b in zip(dense,dense[1:]):lengths.append(lengths[-1]+(b-a).length)
   total=lengths[-1];targets=[0.,.0005,.0012,.0025,.0045,.0075]
   targets.extend(.0075+(total-.0075)*i/7 for i in range(1,7))
   prefix=[];index=0
   for travel in targets:
    while index<len(lengths)-2 and lengths[index+1]<travel:index+=1
    f=(travel-lengths[index])/max(1e-8,lengths[index+1]-lengths[index]);p=dense[index].lerp(dense[index+1],f)
    hit,normal,ii,dd=tree.ray_cast(C,(p-C).normalized(),.25)
    if hit:
     gap=(p-hit).dot(normal);minimum=.00010+.00028*smooth(travel/.014)
     if gap<minimum:p+=normal*(minimum-gap)
    prefix.append(p)
   guides[label][j]=(prefix+[p.copy() for p in original[6:]],width,seed)
  # The sparse long flyaways share the corrected follicle roots. Keeping their
  # old elevated starts would leave a detached halo over the newly lowered part.
  for j in range(462,494):
   old,width,seed=guides[label][j]
   base=min(range(276,414),key=lambda k:(old_paths[k][0]-old[0]).length_squared)
   corrected=guides[label][base][0];original=old_paths[base];path=[]
   for i,p in enumerate(corrected):
    index=(i-6) if i>=12 else i*.5;k=min(len(old)-2,int(index));f=index-k
    offset=old[k].lerp(old[k+1],f)-original[k].lerp(original[k+1],f)
    path.append(p+offset)
   guides[label][j]=(path,width,seed)
 return guides


def _frame(pts,i,label,across_hint=None):
 tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
 # Across-card direction stays continuous from part to hanging length.
 seed=across_hint.normalized() if across_hint is not None else (Vector((1,0,0)) if label=='Back' else Vector((0,1,0)))
 width=seed-tangent*seed.dot(tangent)
 if width.length<.1:width=Vector((1,0,0))
 width.normalize();normal=tangent.cross(width).normalized();return width,normal


def build_groom(human,rig,existing_hair=None):
 """Return render-source and web-card objects; neither source scene nor export is saved."""
 for o in list(bpy.data.objects):
  if o.get('avatar_groom_role'):bpy.data.objects.remove(o,do_unlink=True)
 if existing_hair:
  existing_hair.hide_render=True;existing_hair.hide_viewport=True
  existing_hair['avatar_export_exclude']=True;existing_hair['avatar_groom_replaced']=True
 _bones(rig);cardsmat=_material_cards();hairmat=_material_strands();guides=_guide_data(human)
 coll=bpy.data.collections.get('NaturalHairGroom') or bpy.data.collections.new('NaturalHairGroom')
 if coll.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(coll)
 scalp_tree=_scalp_bvh(human)
 saved_levels=[(m,m.levels) for m in human.modifiers if m.type=='SUBSURF']
 for m,level in saved_levels:m.levels=m.render_levels
 bpy.context.view_layer.update();source_scalp_tree=_scalp_bvh(human)
 for m,level in saved_levels:m.levels=level
 bpy.context.view_layer.update()
 made=[];rng=random.Random(SEED+12);strand_count=0;cards_count=0;triangles=0
 for label,paths in guides.items():
  verts=[];faces=[];uvcoords=[];strandverts=[];edges=[];radii=[]
  for path_index,(pts,width,seed) in enumerate(paths):
   regular_count=len(paths)-(80 if label!='Back' else 0);is_baby=path_index>=regular_count
   layer_size=regular_count//3;layer_start=(path_index//layer_size)*layer_size
   lo=max(layer_start,path_index-1);hi=min(layer_start+layer_size-1,path_index+1)
   if is_baby:lo=hi=0
   elif label!='Back':
    layer=path_index//layer_size;j=path_index%layer_size;lock=_front_lock_spec(label,layer,j)
    if lock:
     low,high,kind=lock;lo=max(layer_start+low,path_index-1);hi=min(layer_start+high,path_index+1)
    else:
     if _front_lock_spec(label,layer,lo-layer_start):lo=path_index
     if _front_lock_spec(label,layer,hi-layer_start):hi=path_index
   previous=paths[lo][0];following=paths[hi][0]
   hairline_factor=(.70+.30*min((path_index%layer_size)/3.,1.)) if label!='Back' and not is_baby else 1.
   width*=hairline_factor
   frontal_boost=1.+(.32*(1-smooth((path_index%layer_size)/12.)) if label!='Back' and not is_baby else 0.)
   width*=frontal_boost
   start=len(verts);n=len(pts);frames=[_frame(pts,i,label,None if is_baby else following[round(i/(n-1)*(len(following)-1))]-previous[round(i/(n-1)*(len(previous)-1))]) for i in range(n)]
   # Distributed follicles require local tangent frames: neighboring guides
   # no longer start at homologous points along a crown arc.
   for i,p in enumerate(pts):
    if label!='Back' and not is_baby and p.z>=1.460:
     tangent=(pts[min(i+1,n-1)]-pts[max(0,i-1)]).normalized()
     hit,nn,ii,dd=scalp_tree.ray_cast(Vector((0,-.035,1.50)),(p-Vector((0,-.035,1.50))).normalized(),.25)
     if hit:
      across=nn.cross(tangent).normalized()
      if across.dot(frames[i][0])<0:across=-across
      blend=1-smooth(((p-pts[0]).length-.0075)/.025)
      across=(frames[i][0]*(1-blend)+across*blend).normalized()
      frames[i]=(across,tangent.cross(across).normalized())
    if i and frames[i][0].dot(frames[i-1][0])<0:frames[i]=(-frames[i][0],-frames[i][1])
   arclength=[0.]
   for a,b in zip(pts,pts[1:]):arclength.append(arclength[-1]+(b-a).length)
   root_rng=random.Random(SEED+23000+path_index*71+({'L':100,'R':700,'Back':1300}[label]))
   split_root=label!='Back' and not is_baby and path_index<layer_size
   root_bands=9 if split_root else 3
   advances=[root_rng.uniform(.00005,.0010) for _ in range(root_bands)]
   advances[0]=root_rng.uniform(0,.00015);root_rng.shuffle(advances)
   knot=(path_index%layer_size)/8.;ki=int(knot);kf=smooth(knot-ki)
   a=random.Random(SEED+70000+ki*7919+({'L':0,'R':1000,'Back':2000}[label])).random()
   b=random.Random(SEED+70000+(ki+1)*7919+({'L':0,'R':1000,'Back':2000}[label])).random()
   part_density=.40+.60*(a*(1-kf)+b*kf)
   advances=[v*part_density for v in advances]
   angles=[root_rng.uniform(-.0007,.0007) for _ in range(root_bands)]
   root_shifts=[root_rng.uniform(-.00065,.00065) for _ in range(root_bands)]
   def card_point(i,f,band=None):
    p=pts[i];arc=arclength[i];t=((arc/arclength[12]*6) if i<12 else (i-6))/(n-7) if label!='Back' and not is_baby else i/(n-1);across,normal=frames[i]
    w=width*(.80+.20*smooth(arc/.004))*(.85+.15*math.sin(t*math.pi))*(1-.94*smooth((t-.82)/.18))
    # The fine-fiber source occupies a wider root patch because each child
    # has its own lateral follicle offset. Match that coverage in the cards.
    if label!='Back' and not is_baby:w*=1.+.65*(1-smooth((arc-.012)/.035))
    v=p+across*((f-.5)*w)
    if band is not None:
     tangent=(pts[min(i+1,n-1)]-pts[max(0,i-1)]).normalized()
     fade=1-smooth(arc/.0025)
     v+=tangent*(advances[band]*fade)+across*(root_shifts[band]*fade+angles[band]*math.sin(math.pi*min(1.,arc/.0025)))
     if arc<.0075:
      hit,nn,ii,dd=scalp_tree.ray_cast(Vector((0,-.035,1.50)),(v-Vector((0,-.035,1.50))).normalized(),.25)
      if hit:
       signed=(v-hit).dot(nn)
       if i==0 or signed<.00010:v+=nn*(.00010-signed)
    index=len(verts);verts.append(v);uvcoords.append((f,1-t));return index
   if split_root:
    # Nine small staggered root patches match the individual source follicles.
    # Extra topology stays within the first 2.5 mm of the innermost cohort.
    previous=None
    for i in range(3):
     row=[]
     for band in range(root_bands):row.append([card_point(i,band/root_bands,band),card_point(i,(band+1)/root_bands,band)])
     if previous:
      for a,b in zip(previous,row):faces.append((a[0],a[1],b[1],b[0]))
     previous=row
    merged=[card_point(3,k/root_bands) for k in range(root_bands+1)]
    for band in range(root_bands):faces.append((previous[band][0],previous[band][1],merged[band+1],merged[band]))
    following=[card_point(4,0),card_point(4,1)]
    middle=root_bands//2
    for k in range(middle):faces.append((merged[k],merged[k+1],following[0]))
    faces.append((merged[middle],following[1],following[0]))
    for k in range(middle,root_bands):faces.append((merged[k],merged[k+1],following[1]))
    previous=following
    for i in range(5,n):
     row=[card_point(i,0),card_point(i,1)];faces.append((previous[0],previous[1],row[1],row[0]));previous=row
   else:
    previous=None
    for i in range(n):
     row=[card_point(i,0),card_point(i,1)]
     if previous:faces.append((previous[0],previous[1],row[1],row[0]))
     previous=row
   cards_count+=1
   # Fibers use the same guide volume, but are independent real tapered curves.
   fiber_count=6 if is_baby else max(9,round(35*hairline_factor*frontal_boost))
   for j in range(fiber_count):
    off=(j+rng.random())/fiber_count-.5;phase=rng.uniform(0,6.28);rad=rng.uniform(.000013,.000023) if is_baby else rng.uniform(.000027,.000046)
    first=len(strandverts)
    lengthmul=rng.uniform(.94,1.)
    band=min(root_bands-1,max(0,int((off+.5)*root_bands)));advance=advances[band]+root_rng.uniform(0,.0004)*part_density
    root_side=root_rng.uniform(-.0008,.0008)
    for i,p in enumerate(pts):
     t=((arclength[i]/arclength[12]*6) if i<12 else (i-6))/(n-7) if label!='Back' and not is_baby else i/(n-1);across,normal=frames[i]
     jitter=.00008*math.sin(t*17+phase)+.00004*math.sin(t*43+phase*2)
     lift=.00015*math.sin(phase+t*9)+.0001*math.sin(t*28+phase)
     root_taper=.80+.20*smooth(arclength[i]/.004)
     loc=p+across*((off*width+jitter)*root_taper)+normal*(lift*smooth(arclength[i]/.012))
     if label!='Back' and not is_baby and arclength[i]<.010:
      tangent=(pts[min(i+1,n-1)]-pts[max(0,i-1)]).normalized()
      fade=1-smooth(arclength[i]/.010)
      loc+=tangent*(advance*fade)+across*(root_side*fade+angles[band]*math.sin(math.pi*min(1.,arclength[i]/.010)))
     # Fine broken flyaway silhouette; never a broad separate sheet.
     if j==0 and seed>.72:loc+=normal*(.0028*math.sin(t*math.pi)**2)
     # Small oval fiber bundles round the front-lock cross section.
     if label!='Back' and not is_baby and _front_lock_spec(label,path_index//layer_size,path_index%layer_size):
      loc+=normal*(width*.18*math.sin(phase*3)*math.sqrt(max(0.,1-(off*2)**2))*smooth(arclength[i]/.03))
     if t>.75:loc.z+=(1-lengthmul)*(t-.75)*(.01 if is_baby else .55)
     # Source and browser body subdivisions differ by up to 0.34 mm.
     # Keep source follicles just clear of the actual render scalp as well.
     if label!='Back' and not is_baby and loc.z>1.478 and arclength[i]<.025:
      hit,nn,ii,dd=source_scalp_tree.ray_cast(Vector((0,-.035,1.50)),(loc-Vector((0,-.035,1.50))).normalized(),.25)
      if hit:
       depth=(loc-hit).dot(nn)
       if i==0 or depth<.000035:loc+=nn*(.000035-depth)
     strandverts.append(loc);radii.append(rad*(.55+.45*smooth(arclength[i]/.004))*(1-.985*smooth((t-.82)/.18)))
     if i:edges.append((first+i-1,first+i))
    strand_count+=1
  mesh=bpy.data.meshes.new('GroomCardsMesh.'+label);mesh.from_pydata(verts,[],faces);mesh.update()
  uv=mesh.uv_layers.new(name='FiberUV')
  for p in mesh.polygons:
   p.use_smooth=True
   for li in p.loop_indices:uv.data[li].uv=uvcoords[mesh.loops[li].vertex_index]
  ob=bpy.data.objects.new('HairCards.'+label,mesh);coll.objects.link(ob);mesh.materials.append(cardsmat)
  ob['avatar_groom_role']='web_cards';ob['avatar_export_include']=True
  ob['hair_chain']=json.dumps(CHAINS[label]);ob.hide_render=True;_skin(ob,rig,label,verts)
  made.append(ob);triangles+=sum(len(face)-2 for face in faces)
  mesh=bpy.data.meshes.new('GroomEditableStrandPoints.'+label);mesh.from_pydata(strandverts,edges,[]);mesh.update()
  radius=mesh.attributes.new(name='strand_radius',type='FLOAT',domain='POINT');radius.data.foreach_set('value',radii)
  points=bpy.data.objects.new('HairGuidePoints.'+label,mesh);coll.objects.link(points)
  points['avatar_groom_role']='source_guides';points['avatar_export_exclude']=True;points.hide_render=True
  _skin(points,rig,label,strandverts);made.append(points)
  curves=bpy.data.hair_curves.new('GroomTrueCurves.'+label)
  source=bpy.data.objects.new('HairStrands.'+label,curves);coll.objects.link(source)
  source['avatar_groom_role']='source_curves';source['avatar_export_exclude']=True
  source['source_note']='Native hair curves derived from armature-deformed editable edge guides.'
  _curve_nodes(source,hairmat,points);made.append(source)
 bpy.context.scene['groom_inventory']=json.dumps({'guides':cards_count,'strand_curves':strand_count,'web_triangles':triangles,'chains':CHAINS,'part_offset_m':.0075,'front_lock_guides':41,'front_lock_contact_bone':'spine01','revision':'distributed_scalp_emergence_v18_selected','seed':SEED})
 print('GROOM_BUILT',bpy.context.scene['groom_inventory'],flush=True)
 return made


if __name__=='__main__':
 human=bpy.data.objects.get('AvatarBody');rig=bpy.data.objects.get('AvatarRig')
 if not human or not rig:raise RuntimeError('Load a character scene before running groom.py.')
 build_groom(human,rig,bpy.data.objects.get('Hair'))
 scene=bpy.context.scene;scene.cycles.samples=32;scene.cycles.use_denoising=False
 scene.render.resolution_x=700;scene.render.resolution_y=856
 scene.render.filepath=str(ROOT/'renders/groom/portrait-strands.png')
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/groom-development.blend'))
 bpy.ops.render.render(write_still=True)
