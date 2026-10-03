# Root-flow geometry refinement

## Selected result

`groom-selected.py` is the frozen V18 candidate, SHA256 `67cc1266e88ae668abefd5787abbfb5aa3171cbf16ac18487d336a6595815ac0`. Its identical versioned source is `groom-v18.py`; `groom_candidate.py` is also an identical convenience copy. The inspectable source is `scenes/groom-root-flow-selected.blend` (identical geometry to `groom-root-flow-v18.blend`). This isolated study left the working source unchanged. The selected module was subsequently integrated into the current build.

The deep black part incision is replaced by a shallow, irregular skin-visible part with individual root emergence. This is a meaningful local improvement in both native source and cards. It does **not** establish photorealism: the card derivative remains comparatively smooth and shiny, the frontal boundary is rather hard, and the long front locks retain a ribbon/string-like character. The part remains more orderly than the reference. No albedo correction, bright scalp patch, new texture, external asset, or source-only material trick is included.

## Geometry changes

- The old first side-guide points floated 1.94–7.40 mm above the scalp, with a median near 4.66 mm. They are now scalp-fitted follicle patches rather than stacked elevated banks.
- Side guide cohorts have deterministic two-dimensional root placement. Individual native strands also have their own longitudinal/lateral root offsets and slightly different emergence directions.
- The first root samples resolve approximately 0, 0.5, 1.2, 2.5, 4.5 and 7.5 mm of travel. A local cubic transition rejoins the original groom after its sixth guide segment.
- The innermost card cohort has nine staggered root branches over its first 2.5 mm, merging into the original long card. Card root coverage includes the lateral footprint occupied by scattered source follicles. The existing procedural fiber atlas is reused unchanged.
- Native source follicles are fitted against the source body's render subdivision, rather than assuming the browser subdivision is coincident. The inspected root clearance is about 35 micrometres on that source surface.
- Local scalp-derived frames blend back to the original frames outside the root region. The selected implementation preserves all 25,004 tested mature side-guide points and all posterior guide positions exactly.
- Sparse long flyaways inherit the corrected roots, removing the detached halo produced when their former elevated roots were retained.
- Front shoulder-lock paths, their contact strategy, secondary bones, API and exporter-facing names/flags are preserved. The small source fiber bundle depth remains; no broad new hairstyle is introduced.

## Why the root-local version was selected

Earlier experiments improved the front part but projected too much of the crown onto the scalp. Side views exposed a shelf/fold where that compressed crown rejoined free-hanging lengths. Frame blending and a gravity-envelope test did not adequately repair that tradeoff. Those whole-crown variants are rejected. V18 confines the change to the roots and retains the previously reviewed mature flow, including the shoulder contact geometry. Earlier V1/V2 broad root dispersion also exposed an excessive bald stripe; those were rejected.

## Fixed visual evidence

The complete before/after path map is in `selection.json`.

- Before: `renders/groom/root-flow/baseline-clean-{source,cards}-{close,three-quarter,profile}.png`
- Selected after: `renders/groom/root-flow/v18-{source,cards}-{close,three-quarter,profile}.png`

All six selected images and the before views were directly inspected. `StudioFloor` is hidden in both before and after diagnostic passes. Cameras, lights, exposure, material setup and character fixture are fixed between each pair. Native source uses body render subdivision 2; cards use subdivision 1. Both use 48 Cycles samples with denoising disabled. Closeups are 900×900; side/three-quarter views are 800×1000. The source fixture predates the newer lash/lid cleanup, so the final integrated character still needs its own comparison.

`render_candidate.py` records exact camera positions and can reproduce the controlled views. The isolated saved scene preserves the build state; the diagnostic floor visibility and final camera positions are applied by the renderer, not to the master.

## Verification

`final-audit.json`:

- 1,333 logical guides; 42,285 native strand curves
- 115,982 actual card triangles, including explicitly triangulated root transitions
- Zero zero-area card triangles
- Exact normalized weights; fixed upper roots are head-only
- 5,401 sampled fixed roots follow 25° head yaw within 0.000000121 m
- 29,250 tested regular side-strand roots clear the source scalp; no penetration beyond the 1-micrometre tolerance

`backbone-preservation.json`: zero positional change over 25,004 mature side-guide points and all posterior guide points.

`final-contact-stress.json`: seven original neutral/yaw/spring cases, zero tested front-contact penetrations, minimum clearance 5.323 mm. This is explicitly a front-contact check, not whole-hair collision certification. The parent has subsequently expanded the integrated check to 19 cases; that result should supersede this isolated seven-case report.

## Integration contract and remaining gates

Copy the selected module into `scripts/blender/groom.py`, then call `build_groom(human, rig, existing_hair)` after final cloth modifiers and arm pose, as the current main builder already does. The root path discovery works from either its QA location or the Blender scripts directory. The function still returns the same nine objects, with the same three card meshes, three source-guide meshes and three native-curve objects. Material names, hair bones, `avatar_groom_role`, inclusion/exclusion flags and the public interface are unchanged. There are no new material/object categories or textures to add to the exporter.

The parent must perform the integrated rebuild, expanded contact test, actual GLB export/re-import and final browser appearance review. None of those later gates is claimed here. The candidate is frozen for that pass; no further unrelated groom edits are planned.
