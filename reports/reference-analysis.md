# Reference fitting analysis

## Useful result

The neutral reference has a softly tapered oval face, broad upper cheeks, a rounded narrow chin, dense nearly straight brows, almond brown eyes, a compact rounded nose, closed relaxed lips, and straight dark-brown hair with a narrow slightly off-center part. The initial anatomical MPFB model is reasonably close in eye spacing; likeness depends heavily on the lower jaw, mouth/nose proportions, brows, hairline, skin color and lighting.

Two input images were processed **locally**, without uploading or modifying them. MediaPipe 0.10.21 produced 478 face/iris points on each. Raw normalized coordinates, pixel coordinates, semantic anchors, input checksums and reliability notes are in:

- `reference/Gemini_Generated_Image_8acbj88acbj88acb.landmarks.json`
- `reference/Gemini_Generated_Image_j1wmblj1wmblj1wm.landmarks.json`
- `reference-analysis.json` adds approximate manual hairline/profile controls and practical fit guidance.

## Neutral front targets

The source is 928 × 1152 pixels. Image-left/right labels describe screen sides, not biological sides or an assumption about mirroring.

| Feature | Measured image value | Ratio to cheek width |
|---|---:|---:|
| Cheek width | 337.5 px | 1.000 |
| Interiris distance | 160.0 px | 0.474 |
| Intercanthal distance | 88.5 px | 0.262 |
| Eye fissure width | about 69 px each | about 0.204 |
| Nasal base width | 80.1 px | 0.237 |
| Mouth width | 127.0 px | 0.377 |
| Jaw landmark span | 256.3 px | 0.760 |
| Nose root to subnasale | 120.0 px | 0.355 |
| Eye line to subnasale, vertical | 111.7 px | 0.331 |
| Subnasale to mouth slit, vertical | 48.6 px | 0.144 |
| Mouth slit to chin, vertical | 102.4 px | 0.303 |

High-use anchors: irises approximately (388.4, 353.9) and (548.4, 352.8); mouth corners (404.0, 513.0) and (530.9, 509.9); nose-tip landmark 1 (465.1, 450.4); chin (468.9, 615.9). These are detector results, not millimeter measurements.

## Comparison with the first anatomical baseline

`reference-baseline-comparison.json` removes crop, scale and roll using the two iris centers and also compares ratios normalized to cheek width. It was computed from the original `portrait-baseline.png`; the original annotated image is preserved as `reference-baseline/portrait-baseline.landmarks.png`. The attempted unannotated copy `portrait-calibration.png` was made after the builder changed cameras and must not be used for old-camera calibration. The original detector JSON and fixed projection dump remain consistent and drive the bake.

Relative to that baseline, the reference suggests:

- Lower jaw span approximately **7% narrower**
- Mouth approximately **4.7% wider**
- Nasal base approximately **5.5% wider**
- Root-to-subnasale approximately **4.8% longer**
- Subnasale-to-mouth slit approximately **11.8% shorter**
- Interiris span only **1.5% wider**, so broad eye enlargement is not indicated
- A fuller lower lip relative to the upper; both initial model lip heights are slightly larger overall than the detector target

These are low-amplitude fitting directions. Apply partial strength first, average symmetric changes, then inspect both front and profile. The baseline's visible chest/garment intersections were also reported to the main builder and must be corrected before review.

## Critical limits

1. The generated references are not a calibrated multiview capture and do not uniquely define a metric head. Small inconsistencies must be regularized rather than exactly copied.
2. The supplied “profile” is near-profile: the far eye remains visible. Do not treat it as an orthographic 90° side image.
3. MediaPipe point 10 is a forehead face-oval control, **not a hairline**. It falls at y227 in the front image while the visible part/hairline apex is near y157. A model built with point 10 as the hairline would have incorrect forehead/hair proportions.
4. The profile chin point is near y660, about 29 px above the visible bottom. Hidden-side landmarks and predicted depth are inferred, not observed. The manually reviewed visible silhouette is a better soft constraint there.
5. MediaPipe z has weak-perspective normalized units; it is not scanned depth. Preserve the source anatomy, mouth cavity, eyeballs and full cranium.
6. The front face is only about 338 px wide. A 4096² atlas can retain those colors in a practical UV layout but cannot add authentic 4K skin detail. Properly licensed generic microdetail remains a separate layer.
7. Reference RGB includes the studio illumination and specular response. It is not intrinsic skin albedo and can produce double lighting under strong relighting.

## Practical fitting/projection workflow

1. Match camera roll, framing, face rotation and long-lens perspective before fitting proportions.
2. Keep the real anatomical source; establish homologous mesh landmarks rather than replacing it with the detector's coarse face surface.
3. Adjust cheek/jaw/chin shape, then eyes/lids, nose, philtrum and lips, using regularized local changes with boundary constraints. Check silhouette at front, profile and three-quarter.
4. Use the supplied photo for a restricted front-facing color layer after alignment. The existing full-head UV atlas remains authoritative.
5. Exclude photo hair/background and eyeball apertures; use body-surface depth tests, front-normal attenuation and a broad facial edge feather. Preserve original ears, scalp, neck and side head.
6. Tone-match the original skin so transitions at jaw, neck and ears are not abrupt. Keep roughness and skin normals independent of the photo.

## Reproducibility

Dependencies are isolated in `.tools/mediapipe`; they are development tooling and must not be committed or shipped. `scripts/reference/requirements.txt` records the three relevant pins. The old MediaPipe version is intentional because it includes the offline legacy FaceMesh model.

```
PYTHONPATH=.tools/mediapipe python scripts/reference/extract_landmarks.py
python scripts/reference/build_analysis.py
python scripts/reference/fit_helpers.py
python scripts/reference/compare_landmarks.py \
  reports/reference/Gemini_Generated_Image_8acbj88acbj88acb.landmarks.json \
  reports/reference-baseline/portrait-baseline.landmarks.json \
  --out reports/reference-baseline-comparison.json
```

`fit_helpers.py` supplies a tested weighted similarity transform, conservative Gaussian sparse-displacement interpolation and a diagnostic front-camera UV projection. It never edits a Blender scene. All helper self-tests and Python syntax checks passed. Source-to-target semantic vertex mapping remains the caller's responsibility.

## Primary method sources

- [Google MediaPipe Face Mesh documentation](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/face_mesh.md): landmark inference, coordinate conventions and refined iris mode
- [Official landmark connection definitions](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/python/solutions/face_mesh_connections.py): feature topology

Visual feature descriptions and manual controls were derived directly from the supplied images. The photo-to-texture experiment and its exact calibration/checksums have a separate report in `reference-bake/bake-report.json`.

## Photo-color deliverables and controlled lighting alternative

- `assets/textures/skin-reference-color.png`: 4096² best initial reprojected color map, with globally tone-matched CC0 skin outside the photo patch
- `assets/textures/skin-reference-mask.png`: exact feathered photo contribution, with eye apertures and disconnected oral/helper islands excluded
- `assets/textures/skin-base-tonematched.png`: the color-matched original skin alone
- `assets/textures/skin-reference-soft.png`: separate conservative illumination-reduced alternative; the best initial map is byte-for-byte preserved

The soft alternative robustly fits a quadratic L* field to 35,783 clean skin pixels, excluding the eyes, brows, nose and lips. It removes 45% of broad illumination, with a ±5 L* field cap, and mildly lifts broad nose/under-brow shadow bands while protecting dark feature cores. Lab chroma is retained before RGB conversion. Actual final face changes range from −4.62 to +6.12 L*, with a +0.15 mean. This is not physical inverse rendering or recovered intrinsic albedo. Duplicate eyebrow/lash geometry still requires scene-side changes.

```
PYTHONPATH=.tools/mediapipe python scripts/reference/bake_reference_color.py
PYTHONPATH=.tools/mediapipe python scripts/reference/verify_bake_roundtrip.py
PYTHONPATH=.tools/mediapipe python scripts/reference/soften_reference_lighting.py
```

The main baker refuses a changed fixed camera-projection checksum to prevent silent mismatched calibration. Full UV→camera roundtrip QA reproduces the warped photo within 1.34 RGB levels mean absolute error and 3 levels at the 95th percentile on 25,137 high-strength pixels. This checks registration rather than realistic lighting. Python syntax, helper tests, output PNG decoding/dimensions and JSON validation passed. The builder's first Blender application of the photo-derived map was visually inspected; the later softened variant still needs the builder's relit front/three-quarter review.

Side-by-side previews, original on the left and softened on the right, are `reference-bake/soft-vs-original-reference-face.png` and `reference-bake/soft-vs-original-atlas-face.png`. Numerical method details and limitations are in `reference-bake/soft-lighting-report.json`.
