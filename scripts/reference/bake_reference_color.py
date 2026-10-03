#!/usr/bin/env python3
"""Bake local reference-photo facial color into an existing anatomical UV atlas.

The output is a reprojected reference texture, not a scan or de-lit albedo.
No original is modified, no reference is uploaded, and no Blender scene is edited.
Run with the isolated extraction dependencies:
  PYTHONPATH=.tools/mediapipe python scripts/reference/bake_reference_color.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from scipy.interpolate import LinearNDInterpolator

from fit_helpers import similarity_2d

ROOT = Path(__file__).resolve().parents[2]


def smoothstep(low, high, value):
    x = np.clip((value - low) / (high - low), 0, 1)
    return x * x * (3 - 2 * x)


def triangle_pixels(p, width, height):
    p = np.asarray(p, dtype=np.float64)
    left = max(0, int(np.floor(p[:, 0].min())))
    right = min(width - 1, int(np.ceil(p[:, 0].max())))
    top = max(0, int(np.floor(p[:, 1].min())))
    bottom = min(height - 1, int(np.ceil(p[:, 1].max())))
    if left > right or top > bottom:
        return None
    matrix = np.array([p[1] - p[0], p[2] - p[0]]).T
    det = np.linalg.det(matrix)
    if abs(det) < 1e-8:
        return None
    yy, xx = np.mgrid[top:bottom+1, left:right+1]
    pair = np.stack((xx - p[0, 0], yy - p[0, 1]), axis=-1) @ np.linalg.inv(matrix).T
    bary = np.concatenate((1 - pair.sum(axis=-1, keepdims=True), pair), axis=-1)
    inside = (bary >= -1e-5).all(axis=-1)
    if not np.any(inside):
        return None
    return yy[inside], xx[inside], bary[inside]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, default=4096)
    parser.add_argument('--strength', type=float, default=.96)
    parser.add_argument('--out', type=Path, default=ROOT/'assets/textures/skin-reference-color.png')
    args = parser.parse_args()
    size = args.size
    projection_path = ROOT/'reports/face-projection.json'
    expected_projection_sha256 = 'b0b280fa98c67e6234ffe860f76a971ca923970136de3297d1369e7f8589b74b'
    if hashlib.sha256(projection_path.read_bytes()).hexdigest() != expected_projection_sha256:
        raise ValueError('Fixed photo-bake projection changed. Re-extract matching render landmarks and explicitly recalibrate before baking.')
    reference_path = ROOT/'Gemini_Generated_Image_8acbj88acbj88acb.jfif'
    base_path = ROOT/'vendor/assets/skins/young_caucasian_female2/young_lightskinned_female_diffuse2.png'
    ref_landmarks_path = ROOT/'reports/reference/Gemini_Generated_Image_8acbj88acbj88acb.landmarks.json'
    current_landmarks_path = ROOT/'reports/reference-baseline/portrait-baseline.landmarks.json'
    projection = json.loads(projection_path.read_text())
    reference_landmarks = json.loads(ref_landmarks_path.read_text())
    current_landmarks = json.loads(current_landmarks_path.read_text())
    width, height = projection['width'], projection['height']
    if (width, height) != (current_landmarks['image_width'], current_landmarks['image_height']):
        raise ValueError('Projection camera and landmark image dimensions differ')
    reference = cv2.cvtColor(cv2.imread(str(reference_path)), cv2.COLOR_BGR2RGB)
    base = cv2.cvtColor(cv2.imread(str(base_path)), cv2.COLOR_BGR2RGB)
    base = cv2.resize(base, (size, size), interpolation=cv2.INTER_CUBIC)
    r = np.array([[v['pixel_x'], v['pixel_y']] for v in reference_landmarks['landmarks']])
    c = np.array([[v['pixel_x'], v['pixel_y']] for v in current_landmarks['landmarks']])
    align = similarity_2d(c[[468, 473]], r[[468, 473]])
    # External controls stabilize interpolation outside the detected forehead.
    frame = np.array([[0, 0], [width/2, 0], [width, 0], [0, height/2],
                      [width, height/2], [0, height], [width/2, height], [width, height]])
    frame_ref = align['scale'] * frame @ align['rotation'] + align['translation']
    warp = LinearNDInterpolator(np.vstack([c, frame]), np.vstack([r, frame_ref]))
    yy, xx = np.mgrid[:height, :width]
    warped = warp(np.stack([xx, yy], axis=-1)).astype(np.float32)
    source_x, source_y = warped[..., 0], warped[..., 1]
    # A face oval safely excludes hair and background. Its upper edge is the
    # detector forehead, not an assumed hairline; upper forehead keeps base skin.
    face_mask = np.zeros(reference.shape[:2], np.uint8)
    hull = cv2.convexHull(r[:468].astype(np.float32)).astype(np.int32)
    cv2.fillConvexPoly(face_mask, hull, 255)
    interior_distance = cv2.distanceTransform(face_mask, cv2.DIST_L2, 5)
    alpha_ref = smoothstep(3, 30, interior_distance).astype(np.float32)
    # Do not project photographed eyeballs onto skin lids or the back of sockets.
    for ids in ([33,160,158,133,153,145,163], [263,387,385,362,380,374,390]):
        eye = np.zeros(face_mask.shape, np.uint8)
        cv2.fillConvexPoly(eye, cv2.convexHull(r[list(ids)].astype(np.float32)).astype(np.int32), 255)
        outside = cv2.distanceTransform(255-eye, cv2.DIST_L2, 3)
        alpha_ref *= smoothstep(0, 2, outside)
    warped_reference = cv2.remap(reference, source_x, source_y, cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(128,128,128))
    warped_mask = cv2.remap(alpha_ref, source_x, source_y, cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT)
    vertices = {v['index']: v for v in projection['vertices']}
    triangles = [t for t in projection['triangles'] if all(i in vertices for i in t['indices'])]
    # Compute a body-only camera z buffer to reject the far side of the head,
    # occluded ears, inner lip backs and other projected overlaps.
    zbuffer = np.full((height, width), np.inf, np.float32)
    for t in triangles:
        v = [vertices[i] for i in t['indices']]
        points = np.array([a['xy'] for a in v])
        raster = triangle_pixels(points, width, height)
        if raster is None:
            continue
        ys, xs, b = raster
        depth = np.array([a['depth'] for a in v])
        z = 1 / np.sum(b / depth[None, :], axis=1)
        zbuffer[ys, xs] = np.minimum(zbuffer[ys, xs], z)
    atlas_x = np.full((size, size), -1, np.float32)
    atlas_y = np.full((size, size), -1, np.float32)
    atlas_alpha = np.zeros((size, size), np.float32)
    camera_position = np.array(projection['camera']['matrix_world'])[:3, 3]
    face_triangles = 0
    for t in triangles:
        v = [vertices[i] for i in t['indices']]
        points = np.array([a['xy'] for a in v])
        # Only potentially facial triangles need a UV projection.
        if points[:,0].max() < 330 or points[:,0].min() > 565 or points[:,1].max() < 365 or points[:,1].min() > 630:
            continue
        uv = np.array(t['uv'])
        uv[:,1] = 1 - uv[:,1]
        raster = triangle_pixels(uv * (size - 1), size, size)
        if raster is None:
            continue
        ys, xs, b = raster
        dep = np.array([a['depth'] for a in v])
        z = b @ dep
        pixel = (b @ (points * dep[:,None])) / z[:,None]
        x = np.clip(pixel[:,0], 0, width-1).astype(np.float32)
        y = np.clip(pixel[:,1], 0, height-1).astype(np.float32)
        normal = b @ np.array([a['normal'] for a in v])
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-8)
        position = b @ np.array([a['co'] for a in v])
        view = camera_position - position
        view /= np.maximum(np.linalg.norm(view, axis=1, keepdims=True), 1e-8)
        facing = np.sum(normal * view, axis=1)
        visible_depth = zbuffer[np.rint(y).astype(int), np.rint(x).astype(int)]
        visible = z <= visible_depth + .0018
        mask = cv2.remap(warped_mask, x[None,:], y[None,:], cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT)[0]
        alpha = args.strength * mask * smoothstep(.05, .5, facing) * visible
        replace = alpha > atlas_alpha[ys, xs]
        ys, xs = ys[replace], xs[replace]
        atlas_x[ys, xs], atlas_y[ys, xs] = x[replace], y[replace]
        atlas_alpha[ys, xs] = alpha[replace]
        face_triangles += 1
    # Keep the contiguous facial UV island only. Body mesh topology can contain
    # tiny separately mapped oral/helper islands projecting through the lips.
    component_count, components, stats, _ = cv2.connectedComponentsWithStats(
        (atlas_alpha > .001).astype(np.uint8), 8)
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    atlas_alpha[components != largest] = 0
    projected = cv2.remap(warped_reference, atlas_x, atlas_y, cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_CONSTANT)
    # Learn a global base->reference Lab shift from cheek skin only, avoiding
    # brow/lip/eye pigmentation and nose highlights. Original microvariation is
    # retained. This is appearance matching, not an intrinsic-albedo estimate.
    atlas_source_x = cv2.remap(source_x, atlas_x, atlas_y, cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT)
    atlas_source_y = cv2.remap(source_y, atlas_x, atlas_y, cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT)
    cheek = (((atlas_source_x > 343) & (atlas_source_x < 407)) |
             ((atlas_source_x > 530) & (atlas_source_x < 592)))
    cheek &= (atlas_source_y > 395) & (atlas_source_y < 480) & (atlas_alpha > .85)
    if cheek.sum() < 100:
        raise RuntimeError('Insufficient visible mapped cheek samples for color match')
    base_lab = cv2.cvtColor(base.astype(np.float32)/255, cv2.COLOR_RGB2LAB)
    photo_lab = cv2.cvtColor(projected.astype(np.float32)/255, cv2.COLOR_RGB2LAB)
    base_median = np.median(base_lab[cheek], axis=0)
    photo_median = np.median(photo_lab[cheek], axis=0)
    delta_lab = photo_median - base_median
    tone_matched = cv2.cvtColor(base_lab + delta_lab, cv2.COLOR_LAB2RGB)
    tone_matched = np.clip(tone_matched * 255, 0, 255)
    # UV per-triangle coverage can leave subpixel cracks; a small closing and
    # nearest color diffusion fill only those tiny interior gaps.
    covered = (atlas_alpha > .001).astype(np.uint8)
    dilated = cv2.dilate(covered, np.ones((3,3),np.uint8), iterations=1)
    holes = (dilated-covered).astype(np.uint8)
    projected = cv2.inpaint(projected, holes, 2, cv2.INPAINT_TELEA)
    closed_alpha = cv2.morphologyEx(atlas_alpha, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    atlas_alpha = np.maximum(atlas_alpha, closed_alpha * holes)
    result = tone_matched * (1-atlas_alpha[...,None]) + projected.astype(np.float32)*atlas_alpha[...,None]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.out), cv2.cvtColor(np.clip(result,0,255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(args.out.with_name('skin-reference-mask.png')), (atlas_alpha*255).astype(np.uint8))
    cv2.imwrite(str(args.out.with_name('skin-base-tonematched.png')), cv2.cvtColor(tone_matched.astype(np.uint8),cv2.COLOR_RGB2BGR))
    # Compact diagnostics keep the untouched calibration data reproducible.
    diagnostic_dir = ROOT/'reports/reference-bake'
    diagnostic_dir.mkdir(parents=True,exist_ok=True)
    cv2.imwrite(str(diagnostic_dir/'reference-warp-to-calibration.png'),cv2.cvtColor(warped_reference,cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(diagnostic_dir/'reference-warp-face-crop.png'),cv2.cvtColor(warped_reference[350:635,325:575],cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(diagnostic_dir/'reference-photo-mask.png'),(alpha_ref*255).astype(np.uint8))
    cv2.imwrite(str(diagnostic_dir/'atlas-preview.png'),cv2.cvtColor(cv2.resize(result,(1024,1024)).astype(np.uint8),cv2.COLOR_RGB2BGR))
    report = {
        'output': str(args.out.relative_to(ROOT)), 'size':[size,size],
        'method':'Body-only visibility-tested camera projection plus MediaPipe piecewise-affine feature alignment into existing UV atlas',
        'calibration_render':'reports/reference-baseline/portrait-baseline.landmarks.png',
        'calibration_render_note':'Original annotated render is preserved; unannotated portrait-calibration.png was copied after the camera-change overwrite and must not be used.',
        'projection_sha256':hashlib.sha256(projection_path.read_bytes()).hexdigest(),
        'reference_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        'base_texture':str(base_path.relative_to(ROOT)),
        'base_license':'CC0, explicitly recorded in adjacent .mhmat',
        'photo_strength':args.strength,'rasterized_candidate_triangles':face_triangles,
        'nonfacial_disconnected_uv_components_removed':component_count-2,
        'covered_atlas_pixels':int((atlas_alpha>.01).sum()),
        'cheek_color_samples':int(cheek.sum()),
        'base_cheek_median_Lab':base_median.tolist(),'photo_cheek_median_Lab':photo_median.tolist(),
        'global_base_Lab_shift':delta_lab.tolist(),
        'limitations':[
            'User-reference reprojection, not a scanned head or calibrated intrinsic albedo.',
            'Source face occupies about 338 pixels across; 4096 atlas preserves layout but does not invent 4K facial detail.',
            'Soft baked illumination/specular remain in the projected photo and can double-light under strong relighting.',
            'Upper forehead, ears, far profile, scalp and body retain color-matched CC0 source texture.',
            'Eye apertures excluded; photographed eyeballs are not deliberately placed onto skin.',
            'This projection was calibrated against the fixed original camera and unchanged head geometry.',
            'The base normals and anatomical geometry remain untouched. Render QA is still required.',
        ]}
    (diagnostic_dir/'bake-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
