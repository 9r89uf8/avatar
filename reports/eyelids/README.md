# Selection update

The v3 geometry has been selected for integration together with the controlled closing-lid diffuse cleanup. Original isolated findings below describe the pre-integration stage. Current build code is `scripts/blender/eyelids.py`; current clean diffuse source is `assets/textures/skin-reference-clean-lids.png`. The selection resolves specific lash/blink defects, not the overall ultrarealism gate.

# Isolated eyelid and lash experiment

## Result

Keep **v3** only as a provisional geometry option. It visibly reduces the original long lower-lash spikes and the upward-pointing lash spikes during closure. It does not establish ultrarealism. The upper lid's pale ridge, the eyes' staring quality, and dark patterned marks across the closed lid remain. The new wetline's benefit is subtle and has not been isolated from the lash change. **No master, build script, eye shader, groom source, production GLB or viewer asset was changed.**

Candidate: `scenes/eyelid-candidate-v3.blend`.

Matched source evidence: `renders/eyelids/comparison-v3.png`, composed without resizing from the six native before/after crops. Individual files are `neutral-before-v1.png`, `neutral-after-v3.png`, `three-quarter-before-v1.png`, `three-quarter-after-v3.png`, `blink-before-v1.png`, and `blink-after-v3.png`. All use the same source camera/lighting/settings per view and 96 Cycles samples with no denoiser. The image crop is 756 x 352 from an 1800 x 2200 render. Neutral and blink share the original portrait camera; the oblique view uses the repository's fixed three-quarter camera.

## Geometry and deformation

The original CC0 lash asset contains 924 disconnected strands (11,088 vertices / 16,632 triangles). The candidate has 396 ordinary tapered mesh strands: 152 upper and 46 lower per eye. The candidate lashes have 9,504 vertices / 17,424 triangles, and the added wetline has 2,328 vertices / 4,640 triangles. This is an appearance experiment, not a mesh-cost optimization; the combined accessory adds 5,432 triangles over the original lashes. The roots use the existing lid-margin correspondence. Shafts have restrained length/diameter variation and fan direction; the lower shafts are shorter. Upper lash direction is explicitly changed during the matching blink rather than retaining an upright neutral vector.

`LidCandidate_Wetline` is a small flattened bead/ribbon approximation along the lid margin. It is an ordinary opaque warm PBR surface with clearcoat, not a physically transmitted tear-film simulation. Optical eye materials and the retained invisible outer eye shell are untouched.

Both objects follow quad Catmull-Clark limit stencils at known original-index lid vertices. The current body modeling-key mix is the resting fit. Both carry the existing six semantic facial keys and a normalized `head` skin group using `AvatarRig`. Rebuild after body modeling changes; do not blindly apply this resting fit to different anatomy or topology. The source has no live dependency on a surface-deform or shrinkwrap modifier, so the portable derivative consists only of ordinary meshes, morphs, materials and skinning.

## Reuse

From a fresh copy of `avatar-master.blend`, add `scripts/eyelids` to the Python path and call `build_candidate.build_lid_candidate()`. It validates the expected topology and identity body transform, rejects duplicate candidate objects, creates two meshes, and hides/marks the original `Lashes` as excluded from export. It does not itself save. Running the script as a main program saves only `scenes/eyelid-candidate-v3.blend`.

The production body/eye/rig, existing lash geometry, shape keys, UVs and material node data match the source fingerprints: `unchanged-source-data-v3.json`. The source `.blend` SHA-256 also remained unchanged during this experiment. `rim-correspondence.json` preserves both sides' exact inner/outer loops, adjacent strip polygons, topology hash and neutral positions for the targeted texture cleanup.

## Structural checks

`validation-v3.json` checks finite coordinates, positive triangle areas, normalized weights and named shape keys. Neutral, full blink, blink plus head turn, and gaze configurations were evaluated numerically. Gaze/combined-pose appearance has not been rendered as a complete production gate.

The isolated portable accessory is `reports/eyelids/eyelid-accessory-v3.glb`. It includes the existing rig and two new meshes, each with six morph targets. Khronos validation reports zero errors and two `NODE_SKINNED_MESH_NON_ROOT` warnings for ordinary rig-parented skinned nodes. Move these meshes through their skin joints; glTF ignores parent-node transforms on skinned geometry. The whole-avatar production export was deliberately not overwritten or rerun.

## Rejected iterations and corrected diagnosis

V1 and v2 were too faint at the review scale. An initial inference that the new shafts were hidden inside the outer lid was **wrong**: a body-only BVH visibility test found every sampled shaft midpoint/tip camera-visible, and `visibility-red-v2.png` showed their positions. Their diameter and overly aggressive taper were the main practical visibility problem. V3 increased shaft diameter and delayed taper. Earlier files remain only as experiment evidence, not accepted alternate geometry.

`blink-after-v2.png` is a useful diagnostic of the separate closed-lid problem: its almost imperceptible geometric hairs leave the stretched dark/scalloped marks on the closed upper lids exposed. `blink-before-v1.png` shows the original geometric spikes on top of those marks. An initial attribution to diffuse color was premature and was withdrawn pending control renders. The completed controls now support it: changing only Skin Base Color to constant removes the vertical/scalloped marks while preserving normal map, roughness, SSS, lashes, geometry and lights. The flat-normal, no-lash and plain-clay controls remain smooth. See `blink-cause-assessment.json`, `blink-cause-cases.json`, and `renders/eyelids/blink-cause-comparison.png`. The narrow diffuse-strip test left the marks unchanged which is consistent with the mask being too narrow; the exact extent still needs a targeted test. The geometry experiment did not edit source skin material or texture pixels.

## Commands

Run from the avatar root with the existing Blender executable:

- `BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b scenes/avatar-master.blend -t 6 --python-exit-code 1 -P scripts/eyelids/build_candidate.py`
- `BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b scenes/eyelid-candidate-v3.blend -t 6 --python-exit-code 1 -P scripts/eyelids/render_candidate_v3.py`
- `BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b scenes/eyelid-candidate-v3.blend -t 2 --python-exit-code 1 -P scripts/eyelids/validate_candidate.py`

Original baseline comparison crops can be reproduced using `render_candidate.py` on the candidate; it switches original/new lash visibility without changing body or eye data. For v3 after-images, use `render_candidate_v3.py`.

## Full portrait scale check

The final 900 x 1100, 64-sample pair is `renders/eyelids/portrait-before-v3.png` and `portrait-after-v3.png`. Both actual images were inspected. The change is a small local improvement in lash restraint, not a substantial gain in overall facial realism. The pale upper margin and staring iris are still prominent at intended portrait distance.

The first full-portrait process was killed with exit 137 during scene loading. No exact global resource limit or OOM cause was established. A two-thread retry completed both images successfully. No diagnostic process saved source material changes.
