"""Apply the small optional anatomy artifact to the matching existing avatar.

Usage from Blender Python:
    from apply_reference_anatomy_fit import apply_reference_anatomy_fit
    apply_reference_anatomy_fit(strength=0.0)  # installs inactive option
    apply_reference_anatomy_fit(strength=1.0)  # preview only after choosing it

Does not save, change materials, refit bones, rebuild the groom, or alter existing
expression keys. Requires the exact matching object topology and MPFB macro mix.
Read reports/fitting/reference-anatomy-v4.json before production integration.
"""
from pathlib import Path
import json,hashlib
import numpy as np
import bpy

ROOT=Path(__file__).resolve().parents[2]

def topology_hash(ob):
    faces=np.array([j for p in ob.data.polygons for j in (len(p.vertices),*p.vertices)],dtype=np.int32)
    return hashlib.sha256(faces.tobytes()).hexdigest()

def apply_reference_anatomy_fit(strength=0.0, artifact_path=None, validate_modeling_keys=True):
    if not 0 <= strength <= 1:raise ValueError('Anatomy strength must be between 0 and 1')
    path=Path(artifact_path) if artifact_path else ROOT/'reports/fitting/reference-anatomy-v4.npz'
    meta=json.loads(path.with_suffix('.json').read_text());data=np.load(path);name=meta['name'];objects=[]
    # Validate everything before editing any object.
    for objname,record in meta['objects'].items():
        ob=bpy.data.objects.get(objname)
        if not ob or ob.type!='MESH':raise ValueError('Missing required mesh '+objname)
        if len(ob.data.vertices)!=record['vertices'] or topology_hash(ob)!=record['topology_sha256']:
            raise ValueError('Topology differs; do not apply vertex-index deltas to '+objname)
        if data[objname].shape!=(len(ob.data.vertices),3) or not np.isfinite(data[objname]).all():
            raise ValueError('Invalid displacement for '+objname)
        objects.append(ob)
    if validate_modeling_keys:
        body=bpy.data.objects['AvatarBody'];keys=body.data.shape_keys.key_blocks
        for key,value in meta['body_modeling_keys'].items():
            # Expressions may be active; they are not part of the permanent shape baseline.
            if key in ['Basis','eyeBlinkLeft','eyeBlinkRight','mouthSmileLeft','mouthSmileRight','jawOpen','browInnerUp']:continue
            if key not in keys or abs(keys[key].value-value)>1e-5:
                raise ValueError('Body modeling mix differs at '+key+'; recalibrate before applying this option')
    for ob in objects:
        if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
        basis=ob.data.shape_keys.key_blocks[0]
        key=ob.data.shape_keys.key_blocks.get(name) or ob.shape_key_add(name=name,from_mix=False)
        key.relative_key=basis
        coords=np.empty((len(basis.data),3),dtype=np.float32);basis.data.foreach_get('co',coords.ravel())
        key.data.foreach_set('co',(coords+data[ob.name]).ravel())
        key.slider_min=0;key.slider_max=1;key.value=float(strength)
        ob['referenceAnatomyFitStatus']='Experimental optional shape; source reports/fitting/reference-anatomy-v4.json'
    bpy.context.view_layer.update()
    return {'strength':float(strength),'objects':[o.name for o in objects],'rig_changed':False,'save_performed':False,'eye_pivot_translation_m_at_strength_one':meta['objects']['Eyes']['rigid_translation_m'],'status':'Experimental only; repeat gaze/combined-expression checks before production use.'}
