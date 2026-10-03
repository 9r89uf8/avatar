#!/usr/bin/env python3
"""Assemble reviewed reference landmarks and manual hairline/profile controls."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONT = 'Gemini_Generated_Image_8acbj88acbj88acb'
PROFILE = 'Gemini_Generated_Image_j1wmblj1wmblj1wm'


def manual_point(name, x, y, uncertainty=6):
    return {'name': name, 'pixel_x': x, 'pixel_y': y, 'x': x / 928, 'y': y / 1152,
            'source': 'manual visual annotation', 'uncertainty_px_approx': uncertainty,
            'z': None, 'not_calibrated_3d': True}


def main():
    front = json.loads((ROOT / f'reports/reference/{FRONT}.landmarks.json').read_text())
    profile = json.loads((ROOT / f'reports/reference/{PROFILE}.landmarks.json').read_text())
    data = {
        'reference_analysis_version': 1,
        'character_scope': 'Clothed adult female character as specified by the build brief; image appearance is not an age estimate.',
        'source_status': 'User-supplied generated reference images, not a calibrated photographic multiview capture.',
        'primary_reference': FRONT + '.jfif',
        'secondary_reference': PROFILE + '.jfif',
        'file_paths': {'front_landmarks': f'reference/{FRONT}.landmarks.json',
                       'profile_landmarks': f'reference/{PROFILE}.landmarks.json'},
        'front_semantic_landmarks': front['semantic_landmarks'],
        'front_measurements': front['measurements'],
        'manual_front_hairline': [manual_point(*v) for v in [
            ('image_left_temple', 300, 334, 10), ('image_left_hairline_1', 319, 282, 8),
            ('image_left_hairline_2', 364, 231, 8), ('image_left_hairline_3', 419, 195, 8),
            ('part_hairline_apex', 491, 157, 5), ('image_right_hairline_1', 536, 199, 7),
            ('image_right_hairline_2', 577, 246, 7), ('image_right_hairline_3', 608, 290, 8),
            ('image_right_temple', 636, 334, 10)]],
        'manual_front_hair_and_ears': [manual_point(*v) for v in [
            ('hair_crown_top', 486, 49, 6), ('part_upper', 493, 92, 6),
            ('part_lower', 491, 147, 5), ('image_left_ear_top', 277, 343, 8),
            ('image_left_ear_bottom', 303, 462, 8), ('image_right_ear_top', 660, 336, 8),
            ('image_right_ear_bottom', 638, 464, 8)]],
        'manual_profile_silhouette': [manual_point(*v) for v in [
            ('frontal_hairline', 695, 199, 7), ('upper_forehead', 724, 270, 7),
            ('brow_ridge', 735, 331, 6), ('nose_root', 728, 375, 7),
            ('nose_ridge_upper', 742, 408, 6), ('nose_ridge_lower', 760, 443, 5),
            ('nose_frontmost', 780, 475, 4), ('nose_lower_tip', 769, 494, 4),
            ('subnasale', 735, 511, 5), ('upper_lip_frontmost', 747, 546, 5),
            ('lip_slit_frontmost', 736, 568, 5), ('lower_lip_frontmost', 743, 585, 5),
            ('labiomental_fold', 722, 614, 6), ('chin_frontmost', 726, 644, 7),
            ('chin_lower_curve', 712, 674, 7), ('chin_bottom', 674, 690, 7),
            ('under_jaw_front', 617, 686, 8), ('under_jaw_neck_transition', 581, 687, 9)]],
        'manual_profile_ear': [manual_point(*v) for v in [
            ('ear_top', 355, 390, 6), ('helix_outer', 340, 442, 6),
            ('ear_lobe_bottom', 411, 550, 7), ('tragus', 411, 471, 7)]],
        'visual_traits': {
            'face': 'Oval with broad softly rounded upper cheeks and tapered lower jaw; rounded narrow chin without a sharply pointed tip.',
            'eyes': 'Almond-shaped brown eyes; upper lid covers upper iris; narrow shadow at upper lash line; clear lower waterline; modest sclera exposure.',
            'brows': 'Dense dark brown, broad inner thirds and largely straight low arch; tapered outer tails. Strong likeness cue.',
            'nose': 'Relatively compact rounded tip, moderate bridge, rounded alar wings, subtle nostril floor. Avoid a sharp triangular or pinched tip.',
            'lips': 'Closed relaxed mouth with gentle cupid bow and fuller lower vermilion; corners slightly elevated. No exaggerated smile.',
            'hair': 'Long straight dark brown, low crown volume, slightly off-center narrow part with fine scalp line; fitted temple transitions; hair tucked behind visible ear in profile.',
            'skin': 'Reference has warm medium-light skin under soft studio lighting; image RGB is not intrinsic albedo. Keep variation around nose/ears/lips and avoid uniform orange or wax-white materials.',
        },
        'fit_priority': [
            'Match lens/framing and face orientation before interpreting shape differences.',
            'Fit head height, cheek width, lower-jaw taper and rounded chin, while preserving anatomical topology.',
            'Fit relative eye spacing and lid aperture, then nasal base width/projection and mouth/philtrum.',
            'Fit real hairline and eyebrow density from manual/photo evidence, not detector forehead point 10.',
            'Validate front, near-profile and three-quarter with the same physical mesh.',
            'Treat model z, occluded contour, ear positions and manually marked profile as soft constraints.',
        ],
        'projection_recommendations': [
            'Use the photo as a restricted front-face color detail layer after geometry and camera fitting, not as a replacement for real mesh anatomy.',
            'Calculate camera projection UVs from fitted camera; keep existing full-head UV atlas for final baking.',
            'Bake only front-visible skin with z-buffer occlusion and a front-normal weight. Feather to original albedo before cheek sides/temples and beyond forehead/lower jaw.',
            'Exclude eye globes, nostril cavities, inner mouth, eyelashes, hair and occluded ears from projected skin color.',
            'Separate color detail from low-frequency lighting; do not transfer baked nostril/lip shadows or nose highlights into normal/roughness maps.',
            'At 928px input width the visible face is only about 338px wide. Upscaling cannot supply genuine pore detail; use properly licensed generic skin microdetail at a separate frequency.',
            'Manual hairline controls form an approximate guide. Follow real hair roots and scalp, and avoid a uniformly thick front shell.',
        ],
        'limitations': [
            'These are generated stills and can disagree in depth, ear shape, hairline and expression. They do not define a unique metric 3D head.',
            'The near-profile reference still shows the far eye and is not an orthographic 90-degree side measurement.',
            'MediaPipe z is weak-perspective inferred depth, not a measured scan; preserve anatomical source depth and regularize any fit.',
            'All manual points have approximate uncertainty in pixels; no hidden or occluded feature is marked as observed.',
            'Profile MediaPipe chin sits about 29px above the visible bottom. Profile inferred far face must not be used as a silhouette.',
            'MediaPipe forehead point 10 is at y227 versus manual visible part/hairline apex y157. It must never set the hairline.',
            'Lighting, exposure, lens and crop have not been calibrated. Skin color numbers must not be treated as true surface reflectance.',
        ],
        'sources': [
            {'title': 'MediaPipe official Face Mesh solution and coordinate conventions', 'url': 'https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/face_mesh.md'},
            {'title': 'MediaPipe official landmark connection definitions', 'url': 'https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/python/solutions/face_mesh_connections.py'},
        ],
    }
    out = ROOT / 'reports/reference-analysis.json'
    out.write_text(json.dumps(data, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
