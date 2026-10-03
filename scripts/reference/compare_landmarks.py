#!/usr/bin/env python3
"""Compare detected landmarks in a render to a reference, independent of framing.

Usage: python scripts/reference/compare_landmarks.py reference.json render.json --out report.json
All geometric results are image-plane estimates, not measurements in mm.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from fit_helpers import similarity_2d


def compare(reference, current):
    ref = np.array([[v['pixel_x'], v['pixel_y']] for v in reference['landmarks']])
    cur = np.array([[v['pixel_x'], v['pixel_y']] for v in current['landmarks']])
    # With two irises, camera roll, framing and global scale are removed without
    # using chin/jaw points whose shapes are precisely what is being measured.
    eye_fit = similarity_2d(cur[[468, 473]], ref[[468, 473]])
    aligned = eye_fit['scale'] * cur @ eye_fit['rotation'] + eye_fit['translation']
    ref_span = np.linalg.norm(ref[473] - ref[468])
    differences = []
    for name, p in reference['semantic_landmarks'].items():
        i = p['index']
        delta = ref[i] - aligned[i]
        differences.append({'name': name, 'index': i,
                            'reference_pixels': ref[i].tolist(),
                            'current_aligned_pixels': aligned[i].tolist(),
                            'desired_delta_pixels': delta.tolist(),
                            'desired_delta_interiris_units': (delta / ref_span).tolist()})
    ratios = {}
    for key, value in reference['measurements']['relative_to_cheek_width'].items():
        baseline = current['measurements']['relative_to_cheek_width'][key]
        ratios[key] = {'reference': value, 'current': baseline,
                       'reference_over_current': value / baseline if baseline else None,
                       'change_percent': (value / baseline - 1) * 100 if baseline else None}
    return {'reference_image': reference['source_file'], 'current_image': current['source_file'],
            'alignment': {'method': 'two iris centers; isotropic scale + roll + translation',
                          'scale_current_to_reference': eye_fit['scale'],
                          'rotation_row_vectors': eye_fit['rotation'].tolist(),
                          'translation_pixels': eye_fit['translation'].tolist()},
            'caveats': ['Only 2D silhouette and feature-projection comparison; depth remains unmeasured.',
                        'Prioritize symmetric averaged changes instead of detector left/right noise.',
                        'Do not drive forehead or hairline from MediaPipe point 10.',
                        'Render skin, hair, camera and light changes can shift automatic detection.'],
            'ratios_normalized_to_cheek_width': ratios,
            'semantic_differences_after_iris_alignment': differences}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('current', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.reference.read_text()), json.loads(args.current.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(args.out)


if __name__ == '__main__':
    main()
