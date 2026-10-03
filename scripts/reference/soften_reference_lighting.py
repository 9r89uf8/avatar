#!/usr/bin/env python3
"""Conservative color-preserving lighting reduction; not intrinsic albedo recovery.

Fits a robust broad quadratic L* field to clean reference skin, excluding eyes,
brows, nose and lips. Removes 45% of that field, capped at +/-5 L*. Small broad
nose/under-brow shadow lifts protect dark feature cores. Applies only through
the existing photo mask; the best original map is never overwritten.
"""
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from scipy.interpolate import LinearNDInterpolator

from bake_reference_color import triangle_pixels, smoothstep
from fit_helpers import similarity_2d

ROOT=Path(__file__).resolve().parents[2]


def features(x,y):
    x=(x-466)/170
    y=(y-421)/200
    return np.stack([np.ones_like(x),x,y,x*x,x*y,y*y],axis=-1)


def gaussian(x,y,cx,cy,sx,sy):
    return np.exp(-.5*(((x-cx)/sx)**2+((y-cy)/sy)**2))


def main():
    original_path=ROOT/'assets/textures/skin-reference-color.png'
    original_hash=hashlib.sha256(original_path.read_bytes()).hexdigest()
    original=cv2.cvtColor(cv2.imread(str(original_path)),cv2.COLOR_BGR2RGB)
    mask=cv2.imread(str(ROOT/'assets/textures/skin-reference-mask.png'),cv2.IMREAD_GRAYSCALE).astype(np.float32)/255
    reference=cv2.cvtColor(cv2.imread(str(ROOT/'Gemini_Generated_Image_8acbj88acbj88acb.jfif')),cv2.COLOR_BGR2RGB)
    ref_lab=cv2.cvtColor(reference.astype(np.float32)/255,cv2.COLOR_RGB2LAB)
    photo_mask=cv2.imread(str(ROOT/'reports/reference-bake/reference-photo-mask.png'),cv2.IMREAD_GRAYSCALE)/255
    yy,xx=np.mgrid[:reference.shape[0],:reference.shape[1]]
    clean=photo_mask>.7
    for cx,cy,sx,sy in [(388,314,83,43),(550,311,83,43),(388,354,65,31),(550,354,65,31),
                        (466,426,60,69),(467,520,84,39)]:
        clean &= (((xx-cx)/sx)**2+((yy-cy)/sy)**2)>1
    clean &= (ref_lab[...,0]>38)&(ref_lab[...,0]<91)
    design=features(xx[clean],yy[clean])
    luminance=ref_lab[...,0][clean]
    weight=np.ones(len(luminance))
    for _ in range(5):
        sw=np.sqrt(weight)
        coefficients=np.linalg.lstsq(design*sw[:,None],luminance*sw,rcond=None)[0]
        residual=luminance-design@coefficients
        scale=max(1,float(np.median(np.abs(residual-np.median(residual)))*1.4826))
        weight=np.minimum(1,2.5*scale/np.maximum(np.abs(residual),1e-6))
    broad=features(xx,yy)@coefficients
    neutral=float(np.median(broad[clean]))
    correction=np.clip(.45*(neutral-broad),-5,5)
    # Broad shadow bands only; near-black brow/lash/nostril/lip cores are protected.
    bands=2.8*gaussian(xx,yy,466,451,43,16)
    bands+=1.8*gaussian(xx,yy,389,335,43,12)+1.8*gaussian(xx,yy,550,333,43,12)
    dark_protection=smoothstep(23,51,ref_lab[...,0])
    lip_protection=1-.7*gaussian(xx,yy,466,519,63,20)
    correction=(correction*lip_protection+bands)*dark_protection
    correction=np.clip(correction,-5,7).astype(np.float32)
    # Reconstruct exactly the same render->photo piecewise map as the main bake.
    p=json.loads((ROOT/'reports/face-projection.json').read_text())
    ref=json.loads((ROOT/'reports/reference/Gemini_Generated_Image_8acbj88acbj88acb.landmarks.json').read_text())
    cur=json.loads((ROOT/'reports/reference-baseline/portrait-baseline.landmarks.json').read_text())
    r=np.array([[v['pixel_x'],v['pixel_y']] for v in ref['landmarks']])
    c=np.array([[v['pixel_x'],v['pixel_y']] for v in cur['landmarks']])
    width,height=p['width'],p['height']
    align=similarity_2d(c[[468,473]],r[[468,473]])
    frame=np.array([[0,0],[width/2,0],[width,0],[0,height/2],[width,height/2],[0,height],[width/2,height],[width,height]])
    frame_ref=align['scale']*frame@align['rotation']+align['translation']
    warp=LinearNDInterpolator(np.vstack([c,frame]),np.vstack([r,frame_ref]))
    y,x=np.mgrid[:height,:width]
    mapped=warp(np.stack([x,y],axis=-1)).astype(np.float32)
    correction_camera=cv2.remap(correction,mapped[...,0],mapped[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    coords=np.where(mask>.001)
    left,top,right,bottom=int(coords[1].min()),int(coords[0].min()),int(coords[1].max()+1),int(coords[0].max()+1)
    atlas_correction=np.zeros((bottom-top,right-left),np.float32)
    vertices={v['index']:v for v in p['vertices']}
    size=original.shape[0]
    for tri in p['triangles']:
        if not all(i in vertices for i in tri['indices']):
            continue
        uv=np.array(tri['uv']);uv[:,1]=1-uv[:,1];uv=uv*(size-1)-[left,top]
        if uv[:,0].max()<0 or uv[:,1].max()<0 or uv[:,0].min()>right-left or uv[:,1].min()>bottom-top:
            continue
        raster=triangle_pixels(uv,right-left,bottom-top)
        if raster is None:
            continue
        ys,xs,b=raster
        valid=mask[ys+top,xs+left]>.001
        if not valid.any():
            continue
        ys,xs,b=ys[valid],xs[valid],b[valid]
        v=[vertices[i] for i in tri['indices']]
        points=np.array([a['xy'] for a in v]);depth=np.array([a['depth'] for a in v])
        z=b@depth
        pixel=(b@(points*depth[:,None]))/z[:,None]
        sample=cv2.remap(correction_camera,pixel[:,0][None,:].astype(np.float32),pixel[:,1][None,:].astype(np.float32),cv2.INTER_LINEAR)[0]
        atlas_correction[ys,xs]=sample
    crop=original[top:bottom,left:right]
    lab=cv2.cvtColor(crop.astype(np.float32)/255,cv2.COLOR_RGB2LAB)
    delta=atlas_correction*mask[top:bottom,left:right]
    lab[...,0]=np.clip(lab[...,0]+delta,0,100)
    softened=np.clip(cv2.cvtColor(lab,cv2.COLOR_LAB2RGB)*255,0,255).astype(np.uint8)
    output=original.copy();output[top:bottom,left:right]=softened
    out=ROOT/'assets/textures/skin-reference-soft.png'
    cv2.imwrite(str(out),cv2.cvtColor(output,cv2.COLOR_RGB2BGR))
    # Side-by-side atlas face crop: identical chroma, controlled L* adjustment.
    preview=np.concatenate([crop,softened],axis=1)
    preview=cv2.resize(preview,(min(1400,preview.shape[1]),int(preview.shape[0]*min(1400,preview.shape[1])/preview.shape[1])),interpolation=cv2.INTER_AREA)
    reports=ROOT/'reports/reference-bake'
    cv2.imwrite(str(reports/'soft-vs-original-atlas-face.png'),cv2.cvtColor(preview,cv2.COLOR_RGB2BGR))
    source_soft=ref_lab.copy();source_soft[...,0]=np.clip(source_soft[...,0]+correction*photo_mask,0,100)
    source_soft=np.clip(cv2.cvtColor(source_soft,cv2.COLOR_LAB2RGB)*255,0,255).astype(np.uint8)
    source_preview=np.concatenate([reference[235:625,295:640],source_soft[235:625,295:640]],axis=1)
    cv2.imwrite(str(reports/'soft-vs-original-reference-face.png'),cv2.cvtColor(source_preview,cv2.COLOR_RGB2BGR))
    assert hashlib.sha256(original_path.read_bytes()).hexdigest()==original_hash
    active=mask[top:bottom,left:right]>.1
    report={'output':str(out.relative_to(ROOT)),'unchanged_original_sha256':original_hash,
            'method':'Robust quadratic illumination field fitted to clean reference-skin L*, 45% removal, +/-5 L* cap; broad nose/under-brow lifts with dark-core protection; a*/b* chroma retained',
            'clean_skin_pixels':int(clean.sum()),'robust_polynomial_coefficients':coefficients.tolist(),
            'reference_L_star_anchor':neutral,'L_star_delta_on_active_face':{'mean':float(delta[active].mean()),'min':float(delta[active].min()),'max':float(delta[active].max())},
            'preserved':['Original best map bytes unchanged','Skin chroma (Lab a*/b*)','Deep brow/lash/nostril/lip core darkness','Original base-tone match and feathered photo mask','Geometry, normal and roughness maps'],
            'limitations':['Conservative appearance adjustment, not physical inverse rendering or true recovered albedo.',
                           'Some baked illumination and occlusion remain intentionally; difficult nose/eye shadows need relit 3D review.',
                           'A quadratic field cannot separate pigmentation, subsurface response, specular and illumination exactly.',
                           'Duplicate eyebrow or lash geometry requires the scene owner to adjust geometry/materials; a texture cannot solve that alone.']}
    (reports/'soft-lighting-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
