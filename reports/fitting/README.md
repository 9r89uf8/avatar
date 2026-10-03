# Conservative multiview anatomy fitting experiment

## Decision scope

This is an isolated geometry experiment, not a new production avatar or an ultrarealism approval. The production master and build scripts were not edited. The final candidate is `scenes/fitting-candidate-v4.blend`; its separate `ReferenceAnatomyFit` shape key can be set to zero or one on the body, brows, lashes and eyes. All existing source topology, UVs, modeling keys, facial expression keys and materials remain present.

The final assessment is in `assessment.json`: modest feature-proportion improvement, but no substantial ultrarealistic identity gain. A subsequent camera-only diagnostic found the original profile comparison too frontal; the earlier anatomical attribution of far-eye exposure and nose/lip contour mismatch is withdrawn. Keep the production default unchanged, preserving this only as an inactive optional shape. Do not use the first three fits as accepted source geometry.

## What was actually fit

- Captured the present MPFB body geometry and the original portrait camera in `base.npz` and `base.json`.
- Extracted fresh landmarks from the current portrait rather than relying on the older comparison report.
- Mapped observed front-face features onto original-index skin triangles with perspective-correct barycentrics. Used verified anatomical vertices for the profile nose, lips and chin; eye-rim mapping is restricted to a homologous, verified MPFB rim triangle where a ray misses the lid.
- Used the exact deltas in the local MPFB target assets, with its X/Z/-Y convention and 0.1 model scale. Left/right eye and cheek targets have shared weights. No MediaPipe depth or generated photo texture was applied.
- Calibrated one weak-perspective camera per generated view using stable visible features, then locked all camera parameters for the final morphology fit. The profile uses visible manual contour annotations and near-eye features, not inferred far-side landmarks or the detector chin.
- Applied bounded least squares with a target-weight prior and a physical surface-displacement prior. The final maximum skin displacement is 2.322 mm and the 95th percentile over head skin is 1.610 mm.
- Preserved attached eyes as rigid translated globes. Brows/lashes receive the same nearby surface displacement as an independently switchable shape. No rig bones were refit; full eye-rotation/binding review would be needed before production integration.

## Important rejected failures

1. A front chin ray grazed the visible chin contour and hit the neck behind it. This let the first fit reduce profile error by using an implausible camera angle. Replaced with a verified chin vertex and actual profile anatomy, and rejected that fit.
2. One detector upper-eyelid point fell inside the eye opening. A skin-only ray reached the orbital wall approximately 30 mm behind the lid. The original front-left upper-lid triangle [4848, 0, 1] was verified to have eye-height target support. The MPFB mirror table maps it to right-lid [11466, 6784, 6785]. This corrected correspondence is used for landmark 386. Correcting it alone reduced the left-oblique baseline residual from 6.62 to 3.45 px. That change is a measurement correction, not an improvement of the avatar.

These failures show why lower automatic landmark loss cannot establish better anatomy.

## Final geometric reprojection checks

All values are RMS per image coordinate in reference-image pixels, with the per-view camera fixed before and after.

| View | Before | After | Change |
| --- | ---: | ---: | ---: |
| Front | 3.672 | 3.216 | -12.4% |
| Right oblique | 4.319 | 3.617 | -16.3% |
| Left oblique | 3.450 | 2.892 | -16.2% |
| Near profile | 5.230 | 5.056 | -3.3% |

These are sparse landmark-fitting results, not a facial-realism score. The generated views are uncalibrated and inconsistent; the small profile change is below the approximate uncertainty of its manual annotations. The head's depth is regularized by the existing anatomy, not measured from the generated images.

## Structural evidence

`mesh-validation-v4.json` records:

- 19,158 source vertices; 26,756 checked body-skin triangles
- 13,711 completely unchanged vertices
- Zero reversed skin triangles in the neutral fit
- Minimum affected triangle area ratio 0.819
- Maximum displacement below the neck 0.0233 mm
- No topology, UV, body-material, reference-image or base-texture replacement

These checks establish neutral geometry continuity only. Rendered blink is checked separately; smile, jaw opening, gaze and combined movements are not a complete production deformation pass for this experimental shape.

## Matched visual evidence

- `renders/fitting/v4/beauty-front-before.png` and `beauty-front-after.png`
- `renders/fitting/beauty-right_oblique-before.png` and `renders/fitting/v4/beauty-right_oblique-after.png`
- `renders/fitting/beauty-profile-before.png` and `renders/fitting/v4/beauty-profile-after.png`
- Clay equivalents isolate geometry from reference color, skin normal and roughness maps
- `renders/fitting/v4/close-after.png` and `close-blink.png` are high-resolution crop checks

The right-oblique and profile before cameras are byte-identical to their original matched-camera settings, so the earlier before renders are valid comparisons. Front before was rerendered after the lid correspondence correction, which changed its calibrated pitch by 0.23 degrees. The high-resolution v3 `close-before.png` uses the earlier front calibration and is therefore only a near-matched diagnostic; do not use it for pixel differencing against v4.

The source master changed while fitting was in progress to include the newer surface relief and updated groom. The frozen local scene keeps the updated groom/materials for both render variants, but resets all anatomy-key weights to the captured source and disables the newly added surface-refinement key. Every render script asserts a baseline geometric match within 0.01 mm before applying this experiment. This prevents the fit from silently mixing later anatomy edits.

## Reproduction

From the avatar root:

1. Fresh-capture step, only when intentionally beginning a new experiment: run `dump_current.py` with Blender against the intended source scene, then extract landmarks with `scripts/reference/extract_landmarks.py` into `reports/fitting/landmarks`.
2. Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/fitting/fit_morphology.py`. This operates on the frozen capture and writes the conservative solution.
3. Run Blender against `scenes/fitting-baseline.blend` with `scripts/fitting/render_v4.py -- beauty 650 64`, or `-- clay 650 64`.
4. Run `scripts/fitting/render_close_v4.py` against `scenes/fitting-candidate-v4.blend` for the close portrait and blink checks.

`fit-v4.json` preserves the final target coefficients and cameras; `fit-v4.npz` preserves the exact vertex displacement. Earlier versions remain only as audit evidence of rejected measurement and fitting routes.

## Compact optional artifact and application test

The `.blend` is a development checkpoint only. To preserve the option in a lightweight source package, keep:

- `reports/fitting/reference-anatomy-v4.npz` (about 158 KB)
- `reports/fitting/reference-anatomy-v4.json` (about 5.6 KB; target settings, topology hashes, expected MPFB macro/modeling mix and eye-pivot shifts)
- `scripts/fitting/apply_reference_anatomy_fit.py`

The function `apply_reference_anatomy_fit(strength=0.0)` installs an inactive option by default. It validates all four mesh topologies and the modeled body mix before editing anything, and never saves the scene. It is idempotent, preserves unrelated keys including `FaceSurfaceRefine`, and transfers the packaged accessory deltas exactly.

`application-test.json` confirms the sequence 0 -> 1 -> 1 -> 0 on the frozen source copy. All pre-existing modeling/expression weights were preserved, and reconstructed displacements matched within 7.46e-9 m. Maximum accessory movements are 0.353 mm at brows, 0.521 mm at lashes, and 0.464 mm at the rigid eye globes. Before production gaze, move the eye.L/eye.R rest pivots by the matching translation in the JSON for the selected strength, then repeat gaze/blink/combined-expression checks. The application helper deliberately does not refit rig bones.

## Actual rendered front ratios

The fresh detector pass on the matched v4 front renders reports improved relative errors for mouth width (-11.4% to -7.8%), nasal-base width (-8.7% to -6.0%) and interiris spacing (-10.1% to -7.6%). Fine measurements are mixed:

- Intercanthal-distance error: -1.3% to -3.8%
- Subnasale-to-mouth-slit interval error: -1.9% to -3.8%
- Right eye-aperture error: -0.5% to -2.7%
- Upper-lip vermilion-height error: +1.0% to +1.7%

The detector also changes estimated iris diameter even though the optical globes only translate rigidly. These fine-ratio changes therefore need visual confirmation and must not be mistaken for exact physical measurements. They are an additional reason to leave this option experimental rather than promote it automatically.

## Final close and blink inspection

The native 740x720 close portrait shows a small proportion change, but does not resolve generic eyelid/orbital anatomy, skin smoothness or the nose/lip profile. The original near-profile triptych was pose-mismatched. The camera-only correction below removes the far-eye discrepancy without anatomy changes, so that comparison cannot establish an anatomical failure. Sparse generated-view fitting still does not establish an identity/ultrarealism upgrade.

The full-blink crop was inspected at anatomy strength 1: both eyes close, with no visible exposed eyeball or obvious detached lashes. The existing lash direction remains artificial. Gaze, smile, jaw opening and combined motions remain unverified for the option.

Recommendation: leave the current master and default unchanged. Preserve only the compact inactive option, its application function and the visual evidence if useful. No further scene promotion was performed.

## Camera-only correction after parent review

The original profile comparison used a 57.6-degree yaw and was too frontal. The earlier inference that excess far-eye exposure demonstrated an anatomical failure was not justified and is withdrawn. The nose/lip silhouette attribution from that pose-mismatched comparison is also unreliable.

`diagnose_profile_camera.py` expanded the camera anchors to include the visible ear top, lobe and tragus, visible near-eye corners, nose-tip silhouette and chin. It held all geometry fixed and fitted only yaw/pitch/roll, scale and translation. Its robust weak-perspective estimate was 71.4 degrees; expanded-anchor RMS fell from 12.52 to 9.02 px. Manual ear uncertainty and generated-view inconsistency mean this is not exact camera calibration.

Three actual renders at 65, 71.4 and 75 degrees confirm the camera effect. At 65 degrees the far eye becomes a narrow sliver, much closer to the reference. At 71.4 and 75 degrees it is almost or entirely hidden. Thus the far-eye exposure difference in the old panel was predominantly pose-confounded. The source remained the captured baseline, with v4 inactive, and every render asserted matching body coordinates within 1e-7 m. No scene was saved.

Corrected evidence:

- `renders/fitting/camera/profile-camera-aligned-comparison.png`: reference, old 57.6-degree baseline view, camera-adjusted 65-degree baseline view
- `renders/fitting/camera/profile-yaw-sweep.png`: reference and all three camera-only renders
- `reports/fitting/profile-camera-diagnostic.json`: anchors, parameters, sensitivity results and corrected interpretation

The old `v4/profile-reference-comparison.png` is superseded for anatomical judgment. The v4 displacement was not refit, changed or promoted. Its original profile residual should not be used as acceptance evidence. The modest front improvements and mixed finer ratios are unchanged, and the optional shape remains inactive.
