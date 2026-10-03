# Visual iteration record

All images are actual rendered geometry unless explicitly labeled as supplied reference images. Source and re-imported GLB images are Cycles renders, not browser screenshots.

1. Initial MPFB baseline: anatomically coherent but stock long01 hair was a grooved shell with a white crown; pale skin; tee penetration at chest. Rejected.
2. Cloth fit: added explicit covered-torso masking, raised collar ribbing and subtle fabric geometry/microrelief. Relaxed arm pose. Chest penetration removed in source render. Background horizon corrected by sizing the review floor appropriately.
3. Reference color: landmark-aligned user-supplied front image projected into anatomical UVs. Improved likeness but introduced some baked illumination. A separate softened lighting variant removes part of a broad robust luminance field; this is not calibrated albedo or scan data. Source face is approximately 338 pixels wide.
4. Skin detail: physically scaled microrelief and varying roughness baked to 4K source maps; explicit 2K browser derivatives reduce memory. No claim that generated noise is captured pores.
5. New hair: replaced visible stock hair with editable tapered strand curves and a separate skinned card derivative. Verified unit weights and head-attached roots. Continued rejection of overly regular crown/part and posterior overlap; further guide refinement underway.
6. Eyes: preserving the source texture's alpha was essential; dropping alpha exposed the original blue transparent-shell atlas region. Physical shell transmission also produced noisy/gray eyes under the current lighting. Controlled coated-eye comparison restores readable iris/pupil and clean catchlights; selected as the stable rendering approximation. Layered geometry remains editable.
7. Face form: measured reference comparisons justify restrained jaw taper, wider mouth/nasal base, adjusted nose length and philtrum, and slight lid/cheek asymmetry. Geometry changes are deliberately small and must repeat portrait and oblique review.
8. Export inspection: a fresh GLB import exposed collar/shoulder deformation missed by the validator. Further inspection found two confirmed causes: clothing viewport subdivision was zero while source rendering used one, and the glTF sheen conversion emitted full white sheen despite a low source weight. The derivative now explicitly bakes clothing subdivision and disables the mismatched sheen extension; armature evaluation is also disabled while baking topology as a precaution. Re-imported render now removes the exaggerated white collar/shoulder sheen.

## Open visual gates

- Final source portrait, three-quarter, profile and full-body review after latest eye/form/groom revisions
- Final GLB re-import appearance after modifier-order correction
- Full blink and smile combinations, including attached lashes
- Actual Babylon appearance and frame-rate measurement; local supported preview routes are unavailable in this executor
- User approval of likeness and realism

The project has not achieved or been certified as ultrarealistic. A successful script, scene save, glTF validation or build is not treated as evidence of that claim.

9. Groom integration order: isolated contact tests passed, but from-scratch regeneration occurred before arm relaxation. Integrated checks found shoulder penetration. Groom creation now runs after final cloth modifiers and pose. Seven tested yaw/secondary-offset cases then passed with zero tested penetrations and minimum 5.32 mm clearance.

10. Exact-current-GLB re-import found residual shoulder/collar creases. A source-versus-GLB vertex comparison measured up to 6.90 mm discrepancy. The noncommuting armature/subdivision order explained part of it; glTF's default four-weight truncation explained the remainder. The delivery pipeline now inverse-skins the desired source garment surface into export-only bind coordinates and explicitly retains eight influences, the maximum consumed by the pinned Babylon loader. The clean re-import then matches shirt and collar within 0.00000061 m, and the actual `cloth-parity-eight-portrait.png` render removes the crease spikes. This does not certify browser appearance or arbitrary full-body animations. `verify_cloth_export.py` guards this neutral-pose parity on subsequent exports.
11. Profile anatomy assessment correction: the original comparison camera was too frontal. With baseline geometry fixed, moving from 57.6 degrees to 65–75 degrees removes most excess far-eye exposure. The old profile panel is superseded by the camera-aligned comparison. The small v4 fit remains inactive because front gains are mixed and generated views are uncalibrated.
12. Synthetic pore-height and tiled jersey studies did not demonstrate meaningful portrait-level improvement; neither is selected. A shaved-scalp color patch also failed to solve the crown incision; current root geometry refinement addresses the measured 2–7 mm floating-root issue instead.

13. Selected integration: surface-root groom V18, restrained lash/wetline meshes, and a UV-baked closing-lid diffuse correction. Constant-color/no-normal/no-lash/clay controls identified the stretched closed-lid pattern as diffuse contamination. The cleanup fixes that specific defect, while neutral eyes now look bare/doll-like; overall realism remains below target. The final 512-sample source portrait makes the smooth/synthetic face and regular hair evident.
14. Final technical checkpoint: all 12 source images packed; GLB: 0 validator errors and 14 hierarchy advisories; 30 tests; source/GLB garment parity; 19 bounded front-contact cases with minimum 5.297 mm clearance. Actual GLB head turn is confirmed at 25 degrees; oblique eyes become gray/reflective and hard hair-bank ends remain visible. These technical passes do not complete the visual or browser gates.
