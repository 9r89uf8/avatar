#!/usr/bin/env python3
"""Offline, reproducible reference analysis. Never uploads or changes inputs.

Install into a project-local or virtual environment with requirements.txt, then:
  python scripts/reference/extract_landmarks.py
  python scripts/reference/extract_landmarks.py path/to/render.png --out reports/render-fit

MediaPipe's z is a weak-perspective estimate, not measured anatomical depth.
The selected reference images have additional manual annotations in analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/avatar-reference-mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/avatar-reference-cache")

import cv2
import mediapipe as mp
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FRONT = "Gemini_Generated_Image_8acbj88acbj88acb.jfif"
PROFILE = "Gemini_Generated_Image_j1wmblj1wmblj1wm.jfif"

# Left/right refer to IMAGE sides, not anatomical sides. Use these semantics
# only after visually reviewing detection; points behind an occlusion are inferred.
SEMANTICS = {
    "nose_tip_lower": 1, "subnasale": 2, "nose_tip_front": 4,
    "nose_bridge": 6, "glabella": 9, "forehead_landmark_not_hairline": 10,
    "upper_lip_center": 0, "mouth_slit_upper": 13,
    "mouth_slit_lower": 14, "lower_lip_center": 17,
    "eye_image_left_outer": 33, "eye_image_left_inner": 133,
    "eye_image_left_upper": 159, "eye_image_left_lower": 145,
    "eye_image_right_outer": 263, "eye_image_right_inner": 362,
    "eye_image_right_upper": 386, "eye_image_right_lower": 374,
    "mouth_image_left": 61, "mouth_image_right": 291,
    "nose_base_image_left": 98, "nose_base_image_right": 327,
    "nose_side_image_left": 129, "nose_side_image_right": 358,
    "temple_image_left": 127, "temple_image_right": 356,
    "cheek_image_left": 234, "cheek_image_right": 454,
    "jaw_image_left": 172, "jaw_image_right": 397,
    "chin": 152, "nose_root": 168,
    "iris_image_left": 468, "iris_image_right": 473,
    "brow_image_left_outer": 70, "brow_image_left_peak": 105,
    "brow_image_left_inner": 107, "brow_image_right_inner": 336,
    "brow_image_right_peak": 334, "brow_image_right_outer": 300,
}


def measure(xy: np.ndarray) -> dict:
    def distance(a, b):
        return float(np.linalg.norm(xy[a] - xy[b]))
    width = distance(234, 454)
    eye_mid = (xy[468] + xy[473]) * .5
    slit = (xy[13] + xy[14]) * .5
    values = {
        "face_cheek_width": width,
        "interiris_distance": distance(468, 473),
        "intercanthal_distance": distance(133, 362),
        "eye_left_fissure_width": distance(33, 133),
        "eye_right_fissure_width": distance(263, 362),
        "eye_left_aperture_height": distance(159, 145),
        "eye_right_aperture_height": distance(386, 374),
        "mouth_width": distance(61, 291),
        "nasal_base_width": distance(98, 327),
        "jaw_width": distance(172, 397),
        "nose_root_to_subnasale": distance(168, 2),
        "eye_line_to_subnasale_vertical": float(xy[2, 1] - eye_mid[1]),
        "subnasale_to_mouth_slit_vertical": float(slit[1] - xy[2, 1]),
        "mouth_slit_to_chin_vertical": float(xy[152, 1] - slit[1]),
        "upper_lip_vermilion_height_center": float(slit[1] - xy[0, 1]),
        "lower_lip_vermilion_height_center": float(xy[17, 1] - slit[1]),
        "iris_left_horizontal_diameter": distance(469, 471),
        "iris_right_horizontal_diameter": distance(474, 476),
    }
    return {
        "units": "image pixels, not millimeters",
        "pixel": {k: round(v, 4) for k, v in values.items()},
        "relative_to_cheek_width": {k: round(v / width, 6) for k, v in values.items()},
        "valid_for_anatomical_comparison": "near-front only; profile values are foreshortened",
    }


def process(path: Path, out: Path, detector) -> dict:
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None:
        raise ValueError(f"Could not read {path}")
    h, w = im.shape[:2]
    results = detector.process(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    record = {
        "source_file": path.name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "image_width": w, "image_height": h,
        "detector": f"MediaPipe {mp.__version__} legacy FaceMesh, refine_landmarks=True",
        "method": "local CPU inference; no reference upload",
        "coordinates": {
            "normalized": "x pixel / width, y pixel / height; origin top-left",
            "depth": "MediaPipe z: smaller = nearer camera; roughly x-normalized scale; not metric",
            "semantic_sides": "image left and image right; no assumption about photograph mirroring",
        },
        "detected": bool(results.multi_face_landmarks),
    }
    if not results.multi_face_landmarks:
        return record
    face = results.multi_face_landmarks[0]
    landmarks = [{"index": i, "x": float(v.x), "y": float(v.y), "z": float(v.z),
                  "pixel_x": float(v.x * w), "pixel_y": float(v.y * h)}
                 for i, v in enumerate(face.landmark)]
    record["landmark_count"] = len(landmarks)
    record["landmarks"] = landmarks
    record["semantic_landmarks"] = {k: landmarks[i] for k, i in SEMANTICS.items()}
    record["measurements"] = measure(np.array([[v["pixel_x"], v["pixel_y"]] for v in landmarks]))
    record["reliability_notes"] = [
        "No per-landmark confidence is exposed by this FaceMesh interface.",
        "Presence of 478 points does not make hidden-side predictions observed evidence.",
        "Landmark 10 marks a forehead oval, not the hairline or the top of the skull.",
        "Contour points on oblique views are projected model locations, not a traced visible silhouette.",
    ]
    if path.name == PROFILE:
        record["reliability_notes"].append(
            "Visual QA: profile chin landmark 152 is about 29 pixels above the visible chin bottom; use manual profile contour.")
    drawing = im.copy()
    for name, connections, color in [
        ("contours", mp.solutions.face_mesh.FACEMESH_CONTOURS, (70, 245, 120)),
        ("iris", mp.solutions.face_mesh.FACEMESH_IRISES, (255, 180, 45)),
    ]:
        mp.solutions.drawing_utils.draw_landmarks(
            drawing, face, connections, landmark_drawing_spec=None,
            connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=color, thickness=1))
    cv2.imwrite(str(out / f"{path.stem}.landmarks.png"), drawing)
    (out / f"{path.stem}.landmarks.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="*", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "reports/reference")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    paths = args.images or [ROOT / FRONT, ROOT / PROFILE]
    manifest = []
    with mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1,
        refine_landmarks=True, min_detection_confidence=.5,
    ) as detector:
        for path in paths:
            record = process(path, args.out, detector)
            manifest.append({k: record[k] for k in ["source_file", "source_sha256", "detected"]})
            print(f"{path.name}: {record.get('landmark_count', 0)} landmarks")
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
