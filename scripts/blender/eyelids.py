"""Portable restrained lashes and lid wetline, selected after controlled renders.

These are artist-authored approximations, not scanned eyelashes or a physically
transmitted tear film. Uses exact quad-limit stencils and the existing six face
morphs. Original asset is preserved hidden and excluded from delivery.
"""
import bpy,sys,math,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
EXPRESSIONS=['eyeBlinkLeft','eyeBlinkRight','mouthSmileLeft','mouthSmileRight','jawOpen','browInnerUp']
INNER=[13365,13363,13364,13369,13371,13359,13352,13353,13358,13357,13356,13355,13354,13377,13376,13375,13379,13366,13374,13373,13372,13370,13368,13367,13378,13362,13361,13360]

def catmull(p,t):
    x=np.clip(t,0,1)*(len(p)-1);i=min(int(x),len(p)-2);u=x-i
    a,b,c,d=p[max(0,i-1)],p[i],p[i+1],p[min(len(p)-1,i+2)]
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)

def material(name,color,rough,coat=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.09;p.inputs['IOR'].default_value=1.4
    m.diffuse_color=(*color,1);return m

def build_eyelids():
    body=bpy.data.objects['AvatarBody'];rig=bpy.data.objects['AvatarRig'];keys=body.data.shape_keys.key_blocks;n=len(body.data.vertices)
    expected_topology='a23e7b4e257c93c127b5e943f5734024076f10851fa227948d0734ec95d41fa5'
    topology=hashlib.sha256(np.array([i for p in body.data.polygons for i in (len(p.vertices),*p.vertices)],np.int32).tobytes()).hexdigest()
    if n!=19158 or topology!=expected_topology:raise ValueError('Lid correspondence does not match the body topology')
    if any(bpy.data.objects.get(name) for name in ['LashesNatural','LidWetline']):raise ValueError('Candidate meshes already exist; start from a clean source copy')
    if not np.allclose(np.array(body.matrix_world),np.eye(4),atol=1e-7):raise ValueError('Recalibrate lid correspondence for a transformed body')
    basis=np.array([p.co[:] for p in keys[0].data]);neutral=basis.copy()
    for k in keys[1:]:
        if k.name not in EXPRESSIONS:neutral+=(np.array([p.co[:] for p in k.data])-basis)*k.value
    states={'Basis':neutral}
    for name in EXPRESSIONS:states[name]=neutral+np.array([p.co[:] for p in keys[name].data])-basis
    adj={i:[] for i in range(n)};fs={i:[] for i in range(n)}
    for e in body.data.edges:
        a,b=e.vertices;adj[a].append(b);adj[b].append(a)
    for face in body.data.polygons:
        for a in face.vertices:fs[a].append(list(face.vertices))
    def stencil(i):
        # Catmull-Clark limit at a manifold all-quad vertex.
        faces=fs[i];degree=len(adj[i]);assert degree==len(faces) and all(len(f)==4 for f in faces)
        out={i:degree*degree}
        for k in adj[i]:out[k]=out.get(k,0)+4
        for f in faces:
            idx=f.index(i);k=f[(idx+2)%4];out[k]=out.get(k,0)+1
        den=degree*(degree+5);return {k:w/den for k,w in out.items()}
    outer=[min([a for a in adj[i] if a not in INNER],key=lambda a:neutral[a,1]) for i in INNER]
    mirror={i:int(np.argmin(((basis-basis[i]*np.array([-1,1,1]))**2).sum(axis=1))) for i in INNER+outer}
    lidpaths={}
    for side in [1,-1]:
        ii=INNER if side==1 else [mirror[i] for i in INNER];oo=outer if side==1 else [mirror[i] for i in outer]
        for typ,inds in [('upper',list(range(15))),('lower',[0]+list(range(27,13,-1)))]:
            lidpaths[(side,typ)]=([stencil(ii[i]) for i in inds],[stencil(oo[i]) for i in inds])
    def curves(state,side,typ):
        v=states[state];ii,oo=lidpaths[(side,typ)]
        calc=lambda ss:np.array([sum(v[i]*w for i,w in st.items()) for st in ss])
        return calc(ii),calc(oo)
    mats=[material('LidWetline_Warm',(.255,.101,.069),.2,.65),material('LashDarkBrown_Restrained',(.012,.007,.0045),.46,.05)]
    generated=[];stats={}
    for role in ['Wetline','Lashes']:
        allstates={name:[] for name in states};faces=[];strand_count=0
        for side in [1,-1]:
            for typ in ['upper','lower']:
                rng=np.random.default_rng(433+side+(100 if typ=='lower' else 0))
                if role=='Wetline':
                    specs=[('line',0)]
                else:
                    count=152 if typ=='upper' else 46
                    ts=np.linspace(.12,.93,count)+rng.normal(0,.0023,count)
                    specs=[(float(t),[float(rng.uniform(.78,1.18)),float(rng.uniform(-1,1)),float(rng.uniform(.80,1.12))]) for t in ts]
                for spec,var in specs:
                    start=len(allstates['Basis']);rings=97 if role=='Wetline' else 6;sides=6 if role=='Wetline' else 4
                    for state in states:
                        inner,outer=curves(state,side,typ)
                        blink=state==('eyeBlinkLeft' if side>0 else 'eyeBlinkRight')
                        if role=='Wetline':
                            points=[];radius=[]
                            for t in np.linspace(.015,.985,rings):
                                inn=catmull(inner,t);out=catmull(outer,t)
                                p=out*.60+inn*.40;p[1]-=.000012
                                p[2]+=(1 if typ=='lower' else -1)*.000045
                                points.append(p);radius.append((.000095 if typ=='upper' else .00013)*(math.sin(math.pi*t)**.45))
                        else:
                            strand_count+=int(state=='Basis');t=spec;inn=catmull(inner,t);out=catmull(outer,t);root=out.copy();root[1]-=.000035;root[2]+=(1 if typ=='upper' else -1)*.000045
                            edge=math.sin(math.pi*t)**.5;length=(.0052 if typ=='upper' else .0025)*edge*var[0]
                            # Fan across the aperture, with short irregular lower hairs.
                            dx=side*((t-.50)*.9+var[1]*.18);dz=(.27+.80 if typ=='upper' else -.43)
                            if blink and typ=='upper':dz=-.37
                            points=[];radius=[]
                            for u in np.linspace(0,1,rings):
                                zshape=(.075*u+.25*u*u) if typ=='upper' else (-.10*u-.11*u*u)
                                if blink and typ=='upper':zshape=-.13*u-.10*u*u
                                p=root+length*np.array([dx*u,-(1.02*u-.05*u*u),zshape]);points.append(p);radius.append((.000046 if typ=='upper' else .000034)*var[2]*(1-.86*u*u))
                        points=np.array(points)
                        for k,(pt,rr) in enumerate(zip(points,radius)):
                            tang=points[min(k+1,len(points)-1)]-points[max(0,k-1)];tang/=max(1e-12,np.linalg.norm(tang));axis=np.cross(tang,np.array([0,-1,0]));
                            if np.linalg.norm(axis)<1e-8:axis=np.array([1.,0,0])
                            axis/=np.linalg.norm(axis);other=np.cross(tang,axis)
                            for a in range(sides):
                                theta=2*math.pi*a/sides;delta=axis*math.cos(theta)+other*math.sin(theta)
                                if role=='Wetline':delta[2]*=.65
                                allstates[state].append((pt+rr*delta).tolist())
                    for k in range(rings-1):
                        for a in range(sides):
                            x=start+k*sides+a;y=start+k*sides+(a+1)%sides;faces.append((x,y,y+sides,x+sides))
                    faces.append(tuple(start+a for a in reversed(range(sides))));faces.append(tuple(start+(rings-1)*sides+a for a in range(sides)))
        mesh=bpy.data.meshes.new(('LidWetline' if role=='Wetline' else 'LashesNatural'));mesh.from_pydata(allstates['Basis'],[],faces);mesh.update();o=bpy.data.objects.new(('LidWetline' if role=='Wetline' else 'LashesNatural'),mesh);bpy.context.scene.collection.objects.link(o)
        mesh.materials.append(mats[0 if role=='Wetline' else 1]);
        for p in mesh.polygons:p.use_smooth=True
        o.shape_key_add(name='Basis')
        for name in EXPRESSIONS:
            key=o.shape_key_add(name=name);key.data.foreach_set('co',np.array(allstates[name],dtype=np.float32).ravel());key.value=0
        group=o.vertex_groups.new(name='head');group.add(list(range(len(mesh.vertices))),1.0,'REPLACE');mod=o.modifiers.new('AvatarRig','ARMATURE');mod.object=rig
        o.parent=rig;o.matrix_parent_inverse=rig.matrix_world.inverted();o['authoredDetail']='Restrained lashes and warm wetline; paired with lid diffuse cleanup. Rebuild after body modeling changes. Human appearance approval pending.';o['surfaceAttachment']='Source all-quad Catmull-Clark limit stencil; semantic facial morphs; head skinning.'
        generated.append(o);stats[role]={'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'triangles':sum(len(f)-2 for f in faces),'strands':strand_count if role=='Lashes' else None,'shapeKeys':EXPRESSIONS}
    original=bpy.data.objects['Lashes'];original.hide_render=True;original.hide_set(True);original['avatar_exclude_export']=True
    return generated,stats

