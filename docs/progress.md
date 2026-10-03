# Build progress

## Current state

A self-contained adult full-body Blender source, rigged GLB and Babylon inspection viewer exist. The model has working blink/smile morphs, a head-turn clip, skinned brow/lash response and a head-attached secondary hair rig. The original upload contained references/research and stray rolldown dependencies, with no prior avatar source or application.

The latest source includes reference-guided facial proportions, a conservatively lighting-reduced reference color map, generated microrelief/roughness maps, clean coated-eye shading, a fitted charcoal tee, and a new asymmetric strand/card groom. It remains visibly synthetic in close portrait review. Ultrarealism and likeness are not approved.

The user confirmed on 2026-10-03 that the project is for personal use, cancelled the proposed licensing inquiry, and reiterated GitHub approval. The current delivery retains only the verified assets; no vendor inquiry, paid-source acquisition or commercial deployment is planned.

## Technical evidence

- Blender 4.3.2 and pinned MPFB 2.0.17 source work in the cloud executor
- Saved source reopens with all required images packed and no missing dependencies
- Production TypeScript build passes; motion, diagnostic and asset-contract tests pass (exact counts in the latest web report)
- GLB loader contract resolves the head, eye joints, nine hair joints and named facial morphs
- Latest checked GLB had zero Khronos errors; warnings and exact asset hash live in reports/gltf-validation.json and subsequent export reports
- Hair root attachment was numerically checked at 25 degrees head yaw; all weights normalize to one
- Source blink closes over the eyes and lashes remain attached; modest smile remains coherent
- Fresh GLB import caught clothing topology/material problems that structural validation did not. Delivery subdivision, sheen conversion and eight-weight/inverse-skin garment correction are now verified in a clean GLB re-import

## Unfinished gates

1. Obtain approval of the visual target after substantive improvement; current source/GLB portrait, profile, full-body and expression comparisons remain visibly synthetic
2. Preserve verified source/GLB garment parity on subsequent exports
3. Substantive character-art refinement remains needed; a new head/material source is only a possible future option, with no procurement or licensing inquiry pending. The permissive Google GNM comparison did not establish a useful quality upgrade
4. Actual Babylon visual and performance QA on a supported browser path
5. User review of the proposed likeness and realism

The cloud Chromium routes failed: localhost was blocked, and the documented internal terminal.local:4173 route returned connection refused. No security controls were disabled or external deployment made. Official Khronos WebGL and WebGL2 capability pages also report graphics support unavailable in the permitted cloud browser. Private preview publication is subject to explicit user authorization and would not by itself establish WebGL support. These are verification limitations, not proof of smooth browser performance.

## Rendering constraints and interpretation

The cloud Blender build has Cycles but no OpenImageDenoise. Source images use explicit samples with denoising disabled. Native hair and the browser card derivative have separate shaders and must be reviewed separately. The face reference has about 338 pixels of horizontal detail; a 4K UV atlas is not a 4K scan. The selected closing-lid diffuse correction and surface-root groom resolve specific defects, but do not meet the overall realism target. All frame-rate, transfer and triangle targets in config/targets.json are provisional engineering goals, not user-approved acceptance thresholds.

See reports/visual-iteration-log.md, reports/source-selection.md and licenses/ASSET-CREDITS.md for complete provenance, changes and limits. This checkpoint is prepared for the user-approved new-branch delivery in 9r89uf8/avatar. No website deployment, purchase or merge is included.
