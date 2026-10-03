# Closing-lid diffuse correction

Controlled constant-color, flat-normal, no-lash and plain-clay renders established that the vertical/scalloped closed-lid marks came from Skin Base Color. Geometry and normal maps were not the cause. Exact evidence is in reports/eyelids/blink-cause-assessment.json.

The first narrow strip and a wider stock-base replacement failed to cover/remove the contamination. The selected variant uses an authored warm skin color in a feathered mask defined over the actual closing-lid surfaces, then bakes it into the ordinary UV albedo. It is not a camera-dependent image overlay. Original atlas texels outside evaluated surfaces are preserved rather than cleared. Source geometry, normals, roughness and eye optics stay unchanged.

Matched results: renders/lid-diffuse-experiment/neutral-closedmask.png and blink-closedmask.png. The dark streaks are removed and the reduced-lash geometry stays attached. A small pale margin ridge and the wider synthetic-face limitations remain. Selection resolves this specific defect, not the ultrarealism gate.

Selected file: assets/textures/skin-reference-clean-lids.png. Exact hashes and limits: selection.json. Reproduce with scripts/blender/review_lid_diffuse.py -- closedmask on the clean eyelid-v3 source (or an equivalent baseline copy retaining the original reference albedo and portrait camera). The mask is authored for this character; do not blindly regenerate after camera, topology or anatomy changes.
