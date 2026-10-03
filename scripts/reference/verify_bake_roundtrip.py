#!/usr/bin/env python3
"""CPU UV->camera roundtrip QA. Diagnostic unlit color, never a final render."""
import json
from pathlib import Path

import cv2
import numpy as np

from bake_reference_color import triangle_pixels

ROOT = Path(__file__).resolve().parents[2]


def main():
    projection = json.loads((ROOT/'reports/face-projection.json').read_text())
    vertices = {v['index']:v for v in projection['vertices']}
    width,height = projection['width'],projection['height']
    color = cv2.imread(str(ROOT/'assets/textures/skin-reference-color.png'))
    mask = cv2.imread(str(ROOT/'assets/textures/skin-reference-mask.png'),cv2.IMREAD_GRAYSCALE).astype(np.float32)/255
    # The builder replaced its working render before an unannotated copy could
    # be saved. The original landmark overlay retains the exact old camera.
    original = cv2.imread(str(ROOT/'reports/reference-baseline/portrait-baseline.landmarks.png'))
    expected = cv2.imread(str(ROOT/'reports/reference-bake/reference-warp-to-calibration.png'))
    if original.shape[:2] != (height,width):
        raise ValueError('Preserved calibration render dimensions changed')
    zbuffer = np.full((height,width),np.inf,np.float32)
    camera_color = np.zeros_like(original)
    camera_alpha = np.zeros((height,width),np.float32)
    for t in projection['triangles']:
        if not all(i in vertices for i in t['indices']):
            continue
        v=[vertices[i] for i in t['indices']]
        xy=np.array([a['xy'] for a in v])
        raster=triangle_pixels(xy,width,height)
        if raster is None:
            continue
        ys,xs,b=raster
        depth=np.array([a['depth'] for a in v])
        z=1/np.sum(b/depth[None,:],axis=1)
        nearest=z<zbuffer[ys,xs]
        if not nearest.any():
            continue
        ys,xs,b,z=ys[nearest],xs[nearest],b[nearest],z[nearest]
        uv=np.array(t['uv'])
        uv=(b@(uv/depth[:,None]))*z[:,None]
        x=(uv[:,0]*(color.shape[1]-1)).astype(np.float32)
        y=((1-uv[:,1])*(color.shape[0]-1)).astype(np.float32)
        sample=cv2.remap(color,x[None,:],y[None,:],cv2.INTER_LINEAR)[0]
        alpha=cv2.remap(mask,x[None,:],y[None,:],cv2.INTER_LINEAR)[0]
        zbuffer[ys,xs]=z
        camera_color[ys,xs]=sample
        camera_alpha[ys,xs]=alpha
    view=original.astype(np.float32)*(1-camera_alpha[...,None])+camera_color*camera_alpha[...,None]
    out=ROOT/'reports/reference-bake'
    cv2.imwrite(str(out/'camera-color-roundtrip.png'),np.clip(view,0,255).astype(np.uint8))
    cv2.imwrite(str(out/'camera-color-roundtrip-face.png'),np.clip(view[350:635,325:575],0,255).astype(np.uint8))
    active=camera_alpha>.9
    error=np.abs(camera_color.astype(float)-expected.astype(float))[active]
    report={'method':'Unlit UV-color CPU perspective rasterization with nearest-depth testing',
            'purpose':'Check photo feature registration survived atlas baking; not realistic lighting QA',
            'visible_high_strength_pixels':int(active.sum()),
            'mean_absolute_rgb_error_vs_warped_source':float(error.mean()),
            'p95_absolute_rgb_error_vs_warped_source':float(np.percentile(error,95)),
            'notes':['Residual includes 4% retained base skin, color blending and raster resampling.',
                     'Backdrop is the preserved original annotated render. Green detector marks are diagnostic only.',
                     'Original hair and eyes remain in the composite; it is explicitly a diagnostic.',
                     'Blender front/profile renders remain required for realistic final evaluation.']}
    (out/'roundtrip-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
