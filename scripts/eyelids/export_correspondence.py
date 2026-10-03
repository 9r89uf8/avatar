import bpy,sys,json,numpy as np,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));from build_candidate import INNER
body=bpy.data.objects['AvatarBody'];keys=body.data.shape_keys.key_blocks;basis=np.array([x.co[:] for x in keys[0].data]);n=len(basis);neutral=basis.copy()
for k in keys[1:]:neutral+=(np.array([p.co[:] for p in k.data])-basis)*k.value
adj={i:set() for i in range(n)}
for e in body.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
outer=[min([a for a in adj[i] if a not in INNER],key=lambda a:neutral[a,1]) for i in INNER]
mirror={i:int(np.argmin(((basis-basis[i]*np.array([-1,1,1]))**2).sum(axis=1))) for i in INNER+outer}
faces=[list(p.vertices) for p in body.data.polygons]
h=hashlib.sha256(np.array([i for p in body.data.polygons for i in (len(p.vertices),*p.vertices)],np.int32).tobytes()).hexdigest()
r={'body':'AvatarBody','source':bpy.data.filepath,'sourceVertices':n,'topologySha256':h,'coordinateSpace':'Body local coordinates; source matrix is identity; meters; +X character left.','ringMeaning':'inner is back edge of existing lid margin, outer is forward edge; paired one-to-one through quad rim. Upper/lower ordered medial to lateral. For texture cleanup test outer_to_next_skin_faces first, expand adjacent strip deliberately.','sides':{}}
for side in [1,-1]:
 ii=INNER if side==1 else [mirror[i] for i in INNER];oo=outer if side==1 else [mirror[i] for i in outer]
 record={}
 for typ,inds in [('upper',list(range(15))),('lower',[0]+list(range(27,13,-1)))]:
  inside=[ii[i] for i in inds];outside=[oo[i] for i in inds];rimset=set(inside+outside)
  strip=[k for k,f in enumerate(faces) if set(f).issubset(rimset) and set(f)&set(inside) and set(f)&set(outside)]
  nexts={i:sorted(adj[i]-set(ii)-set(oo)) for i in outside};nextset=set(outside)|{i for vals in nexts.values() for i in vals}
  ext=[k for k,f in enumerate(faces) if set(f).issubset(nextset) and len(set(f)&set(outside))>=2]
  expanded=set(nextset)
  for i in list(nextset):expanded.update(adj[i])
  expandedfaces=[k for k,f in enumerate(faces) if set(f).issubset(expanded) and set(f)&nextset]
  record[typ]={'inner':inside,'outer':outside,'rim_faces':strip,'rim_face_vertices':[faces[k] for k in strip],'next_skin_neighbors':nexts,'outer_to_next_skin_faces':ext,'outer_to_next_skin_face_vertices':[faces[k] for k in ext],'one_extra_ring_face_candidates':expandedfaces,'neutral_inner_positions_m':neutral[inside].tolist(),'neutral_outer_positions_m':neutral[outside].tolist()}
 r['sides']['positive_x_character_left' if side==1 else 'negative_x_character_right']=record
(ROOT/'reports/eyelids/rim-correspondence.json').write_text(json.dumps(r,indent=2));print('RIM_CORRESPONDENCE_WRITTEN')
for s,records in r['sides'].items():
 for t,rec in records.items():print(s,t,'inner',rec['inner'],'outer',rec['outer'])
