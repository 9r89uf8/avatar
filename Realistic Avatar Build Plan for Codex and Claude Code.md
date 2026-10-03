Build one representative character all the way from Blender to an interactive browser first. The first milestone is an editable full-body source, an uncompressed GLB, and a small viewer showing a portrait, full-body view, blink and head turn. Use that result to choose the asset source and rendering approach before investing in detailed production work.

This plan is for Codex or Claude Code to execute in bounded tasks. It assumes the browser is the final destination because the three supplied documents cover both character production and browser delivery. Default scope is one clothed adult character, portrait-first review, full body available, simple hair, idle, blink, gaze and smile. Follow the toolkit’s adult female brief if that remains the intended character.

The attachments are research documents, not a supplied character, texture pack or working project. Actual source assets, reference images, hardware and asset permissions still need to be established. The stages below are a proposed implementation sequence; they are not completed tests or delivery estimates.

## How the three documents fit together

| Document | Role in the build |
| - | - |
| Blender Avatar Agent Toolkit | Tool setup, local execution, scripting, asset access, version records and repeatability. |
| Realistic Humans in Blender | Anatomy, skin, eyes, hair, clothing, deformation and visual review of the source character. |
| Rendering Realistic Humans in the Browser | Export boundary, runtime materials, controls, compression, device budgets and browser delivery. |

Use the toolkit to establish control of Blender, then run a small source-to-browser experiment. After that succeeds, alternate character improvements with browser checks. This avoids discovering late that a finished groom, shader or facial setup needs substantial conversion.

## Recommended starting architecture

Use Blender with project-owned Python scripts for repeatable jobs. Add one MCP connector when live inspection is useful; a working command-line pipeline can proceed without it. Initially run the coding agent and Blender on the same workstation, or on a deliberately configured shared host.

Start with MPFB and selected system assets when cost and reproducibility are the priorities. Its official setup requires separate assets and advises adding the rig before body parts or garments that should follow it. Use that as a starting route, with portrait quality evaluated on the actual asset. [MPFB setup](https://static.makehumancommunity.org/mpfb/docs/getting_started.html)

For a new browser project, use a small TypeScript viewer; Vite is a reasonable proposed scaffold. Prototype Babylon.js with ordinary glTF PBR first, then compare its skin diffusion on the same character. The official material documentation exposes prepass scattering and warns about its GPU cost; it supports testing the feature, not assuming it will meet this project’s quality or speed requirements. [Babylon material documentation](https://github.com/BabylonJS/Documentation/blob/master/content/features/featuresDeepDive/materials/using/masterPBR.md)

Use WebGL2 as the initial rendering baseline. Evaluate WebGPU only if it will ship, and retain explicit initialization recovery and a poster fallback. If an existing app already uses Three.js, test its current renderer first and change engines only for a demonstrated requirement. Add React integration only if the surrounding app needs React.

Keep two asset representations: an editable Blender master and a separate browser delivery copy. Use GLB for runtime geometry, materials, skinning and supported animation. Store application-specific material intent and control mappings alongside it. A small viewer can be statically hosted; speech services and saved user data introduce separate backend work.

## Phases and completion gates

| Phase | Main result | Advance when |
| - | - | - |
| 0 Define the target | Brief, selected assets and named test devices | Scope and asset access are concrete enough to build. |
| 1 Establish the pipeline | Blender automation, test export and viewer | Save, reopen, render, export and browser load all work. |
| 2 Prove the portrait | Representative face and renderer decision | Eyes, hairline, skin and basic motion pass review on target hardware. |
| 3 Finish the character | Approved source and browser derivative | Full body, clothing and required deformation remain coherent. |
| 4 Add runtime behavior | Idle, blink, gaze and expressions | Controls combine predictably and recover to neutral. |
| 5 Optimize and harden | Low and medium variants, reliable runtime | Quality, performance, failure handling and deployed loading pass. |
| 6 Extend the product | Optional speech and additional features | Each extension preserves the approved visual and runtime behavior. |

Phases 1 and 2 form the feasibility milestone. Phases 3 and 4 form the functional avatar MVP. Phase 5 is the release candidate. Establish a schedule after the source asset and first portrait review reveal the amount of artistic repair required.

## Phase 0 Define the target

Record the character’s adult age range, proportions, skin tone, simple hairstyle, clothing, required expressions and intended camera distance. Use consistent front, profile and three-quarter references. If references are absent, label a neutral test character as provisional; do not invent a confirmed likeness.

Name at least one actual desktop device and, if mobile is in scope, the lowest supported phone, browser and viewport. Record whether users can orbit the camera, change lighting or see several avatars at once. Start with one visible avatar. Define numerical cold-load and 95th-percentile frame-interval thresholds with a named network test profile; provisional targets can be revised after the feasibility experiment.

Choose one human source and inventory its geometry, maps, eyes, mouth parts, rig, expressions and clothing. Retain the relevant asset-level license record and resolve permission to deliver model and texture bytes in a browser before selecting the shipping source. If a candidate cannot be used for that delivery, select a suitable permitted asset before deeper production.

Outputs: `docs/brief.md`, `config/assets.json`, `config/targets.json` and approved references.

Gate: the agent has a usable source asset and a sufficiently specific visual target. Missing paid assets or unavailable target hardware are recorded dependencies; unrelated setup work can continue.

## Phase 1 Establish the pipeline

1. Inspect the real Blender executable, installed extensions, renderer and machine. Query available APIs and connector schemas instead of copying version-specific examples unchanged.

2. Create or import a disposable character with basic materials. Add the MPFB rig before dependent body parts and garments when following that route. Preserve any suitable supplied rig.

3. Save a scene, reopen it in a separate Blender process, inspect missing dependencies and render a fixed portrait. Confirm the agent can actually open the resulting image.

4. Create a separate web export collection or scene. Export a neutral pose plus one short head turn and a blink target or clip. Include a provisional browser-compatible hair representation early.

5. Build one canvas, camera rig, loader and review controls. Add portrait/full-body camera selection, clip playback, a basic expression slider, loading/error states and a backend label.

6. Validate the GLB and compare imported mesh, material, skeleton, clip and morph inventories with the export report.

Proposed scripts: `inspect_environment.py`, `build_character.py`, `inspect_scene.py`, `render_review.py` and `export_avatar.py`. Keep explicit input and output paths, meaningful exit codes, recorded parameters and scene checkpoints.

Outputs: editable test scene, review image, `avatar-uncompressed.glb`, validation JSON and a local viewer. The Khronos validator produces structured issue reports; use those for format checks alongside the separate visual review. [glTF Validator](https://github.com/KhronosGroup/glTF-Validator)

Gate: correct scale, orientation, bind pose, texture resolution paths and named animation data; zero validator errors and reviewed warnings. Repeating the documented steps reproduces the same asset structure and settings. A headless/software browser test establishes loading only; hardware appearance remains a later gate.

## Phase 2 Prove the portrait and choose the renderer

Use the intended human, or a representative candidate with the same important material and animation needs. First approve major anatomy in clay front, profile and three-quarter views. Preserve a full-body source while concentrating detail work on the head and shoulders. Establish stable deformation topology and UVs before substantial texture transfer, groom attachment or expression work.

Establish fixed cameras, lighting, exposure, background and review resolution. Review skin, neck continuity, iris depth, cornea, lid contact, brows, lashes and the simple hairline. Confirm the eyes close and the head turns before expanding the character.

In the browser, get base color, normal and roughness inputs correct before adding scattering. Compare diffusion off and on under soft, directional and back lighting, with light and dark backgrounds. Review ears, nose, lips and silhouette during motion. Keep depth of field off during diagnosis. If WebGPU is proposed for shipping, run the same appearance and motion gate on WebGPU and WebGL2; support detection and successful initialization do not establish acceptable rendering on both.

For Babylon, bind effects only to exact mapped skin materials, verify scene scale, and distinguish diffusion from thin-part translucency. Keep thickness and other masks explicit about UVs, channels and units. Do not expect Cycles shader parameters to transfer numerically.

Record a renderer decision with screenshots, a short motion capture and measured cost on the named device. If the result fails, identify whether the asset, material, lighting or renderer is responsible. Try the least complex correction that addresses the defect. Compare one alternative source only when it is available and the current candidate’s repair burden justifies it.

Outputs: approved portrait evidence, `docs/renderer-decision.md`, versioned material settings and a list of remaining defects.

Gate: a human reviewer approves facial believability at the intended camera distance, and the selected renderer has a credible performance path. If no human review or real device is available, mark that gate pending; do not describe it as passed.

## Phase 3 Finish the character and delivery asset

Complete work in dependency order: large forms and scale, stable deformation topology and UVs, skin and eyes, brows and hair, matching neck/hands/body, then clothing and pose. Preserve working shape keys and vertex correspondence. Rebuild or transfer affected data deliberately if topology changes. Preserve the topology and UV layout established in Phase 2; required changes invalidate affected portrait evidence and must repeat those review checks.

Maintain the detailed Blender master. In its delivery copy, bake the required material inputs, prepare hair cards and lashes, preserve separate eye behavior, and export a deformation skeleton with supported clips and morph targets. Review cloth and hair in motion; simulated Blender behavior needs an explicit delivery representation.

Test full blink, smile, jaw opening, head turn, shoulder lift, elbow/knee bend and any motion the product actually exposes. Review expression combinations, garment contact, foot placement and hand detail. Re-export after each significant visual change.

Outputs: approved source checkpoint, updated uncompressed GLB, texture inventory, review renders and a short deformation sequence.

Gate: the source and browser versions preserve identity and acceptable appearance, with no major visible seams, detached hair, lid gaps, broken joint volume or garment penetration at supported views. Exact Cycles-to-browser pixel matching is not an acceptance criterion.

## Phase 4 Add runtime behavior

Implement a small avatar controller for idle, bounded gaze, blink and smile. Start with manual sliders and deterministic test sequences, then add natural timing and smoothing. Resolve mesh, bone and morph bindings once during loading.

Define which system owns each animated channel. For example, the idle clip owns its body joints, gaze owns the eyes and specified head contribution, and one facial compositor combines expression inputs. Specify limits and conflict behavior so independent systems do not overwrite the same values unpredictably.

Expose a small application API for loading/unloading, selecting a supported expression, setting gaze, playing a supported clip, pausing and choosing quality. The exact names are project choices. Keep scene updates in the render loop and avoid per-frame UI state updates.

Outputs: runtime controller, semantic control map, manual review controls and reproducible motion sequence.

Gate: idle, gaze and expression combinations remain stable; pause/resume and reset work; missing required targets produce a useful diagnostic; unloading removes owned callbacks and resources. Reserve full speech synchronization for Phase 6.

## Phase 5 Optimize and harden delivery

Create distinct low and medium assets from the approved delivery source. Reduce geometry where it does not damage silhouette or deformation, preserve necessary morphs and clips, and tune textures for the actual camera. Keep intermediate exports so regressions can be traced.

Evaluate KTX2 texture compression and meshopt geometry/animation compression in separate steps. glTF Transform provides separate compression, quantization and simplification operations; assess their effects independently and recheck the exported inventory after each transformation. [glTF Transform CLI](https://gltf-transform.dev/cli)

| Proposed starting target from the browser document | Low mobile tier | Medium desktop tier |
| - | - | - |
| Visible avatar triangles | 40,000 to 80,000 | 100,000 to 200,000 |
| Largest face texture | 2K, with a 1K fallback experiment | Up to 4K where visibly useful |
| Initial avatar transfer | 5 to 10 MB | 10 to 20 MB |
| Sustained frame rate goal | 30 FPS | 60 FPS |
| Skin treatment | Portable PBR, diffusion off | Enable diffusion only if measured headroom permits |

These are planning targets, not measured results or universal limits. Count the full frame and runtime texture/render-target costs. File size alone is not a GPU-memory measurement.

Measure cold and warm loading separately, including time to the first correctly shaded avatar. Run the same 60-second camera/motion sequence after warm-up; record median and 95th-percentile frame intervals, stalls, draw calls, backend, viewport, actual render resolution and asset hash. If mobile ships, include a five-minute thermal test. Inspect screenshots and motion beside the numbers.

Complete poster/loading/retry/fallback states, keyboard controls, pause and reduced-motion behavior. Test resize, tab suspension, repeated load/unload, quality changes and graphics failure. If WebGPU ships, force its initialization to fail and verify WebGL2 recovery; if rendering cannot recover, show the poster.

Serve versioned assets over HTTPS and verify the deployed model, textures and decoder files, including paths, MIME types and any required cross-origin configuration. Reject unsupported `extensionsRequired` and missing decoder support before accepting an optimized asset; structural validation does not establish loader compatibility. Preserve animation state during tier changes and dispose the previous variant.

Outputs: versioned delivery variants, benchmark records, lifecycle evidence and a deployed release candidate at the authorized destination.

Gate: the named devices meet the agreed visual and performance targets, loading and failure paths work, and repeated lifecycle operations do not show continuing resource growth. Record hardware checks that remain unavailable.

## Phase 6 Add optional product features

Add speech only after manual facial controls pass. Begin with one prerecorded audio sample and timed visemes, then integrate the selected speech provider. Use actual audio playback time as the clock. Map the provider’s events explicitly to the avatar and test pause, interruption, audio failure and return to neutral.

Add chat/backend behavior, facial tracking, wardrobe changes, multiple avatars, elaborate secondary motion or a portrait/high tier as separate tasks with their own measurable acceptance criteria. Keep purchased tools and custom shaders tied to a demonstrated requirement.

Gate: each new feature preserves the established appearance, frame budget and controller ownership rules.

## Repository handoff for either agent

Use one shared plan and keep the client entry files short.

| Location | Purpose |
| - | - |
| `AGENTS.md` and `CLAUDE.md` | Point to the same brief, plan, commands and progress record. Preserve existing repository instructions. |
| `docs/build-plan.md` | This implementation plan. |
| `docs/research/` | The three supplied research references. |
| `docs/progress.md` | Current phase, completed tasks, evidence, blockers and next bounded task. |
| `config/` | Character settings, assets, targets and tested versions. |
| `scripts/blender/` | Creation, inspection, render, bake and export jobs. |
| `web/src/` | Loader, material setup, controller, quality policy and small review UI. |
| `schemas/` | Validation for the asset manifest and material/control settings. |
| `scenes/`, `exports/`, `renders/` | Source checkpoints, delivery files and review evidence. |
| `reports/` | Validation, inventory and performance results. |

Use appropriate storage for large scene/texture assets, and keep source-only or restricted files outside the browser’s public directory. Track scripts and configurations in version control.

Define two small contracts before the viewer grows. The asset manifest records IDs/hashes, source versions, variant URLs, sizes, required extensions, dimensions, clip names, morph mappings and evidence. The `avatar.web.json` sidecar records schema version, the relevant GLB hash, exact material bindings, per-material map interpretation, camera/light presets and quality overrides. Validate both and reject mismatched asset/settings pairs. Update hashes and bindings after asset transformations.

## How to run the work

Give the agent one bounded task at a time: input checkpoint, exact goal, expected outputs and acceptance evidence. A task is complete when its evidence exists and its required gate has been evaluated.

The coding agent should handle repeatable scene edits, configuration, baking, export, viewer code, numeric checks and evidence capture. Anatomy, likeness, hairstyle design and believable expressions need visual judgment; a better source asset or artist intervention may be more efficient when repeated scripted edits stop improving the result.

Keep one writer per Blender scene. A second agent can build an isolated viewer module, inspect screenshots or review reports against a fixed export contract. It should not mutate the live scene concurrently.

For visual iteration, name the most visible defect, save the best checkpoint, change one variable family, render the same views and keep or revert the change. Proceed autonomously with reversible work covered by the task. Request input only for a concrete missing asset, a consequential scope choice or the appearance review that the milestone requires.

Do not count a successful script, a typecheck or a small thumbnail as proof of realism. Record technical checks, agent visual review, human appearance approval and real-device performance separately.

## First task to paste into Codex or Claude Code

```text
Use the three supplied research documents and this build plan as project context. Begin with Phase 0 and Phase 1 only.

Goal: prove one repeatable Blender-to-browser pipeline for a clothed adult character. Preserve the full-body Blender source and use portrait-first review.

Inspect the existing repository, instructions, installed Blender, available assets and actual hardware before editing. Preserve the existing app stack where practical. Record provisional choices and exact tested versions; treat document version numbers as candidates until verified.

Create docs/brief.md, config/assets.json, config/targets.json and docs/progress.md. Keep AGENTS.md and CLAUDE.md as short pointers to shared project instructions.

Implement scripts to create/import a test character, inspect it, save/reopen it, render a review image and export an uncompressed GLB. Add a minimal TypeScript viewer with fixed lighting, portrait/full-body cameras, a short head turn and a blink control. For a new viewer, begin with Babylon.js and WebGL2 using ordinary PBR materials.

Validate the GLB and compare mesh/material/bone/morph/clip inventories. Open the actual review images. Save commands, logs, screenshots and unresolved defects. Confirm scale, orientation, textures and deformation.

Use one Blender scene writer. Continue all unblocked work if an asset or hardware check is unavailable. Clearly identify any placeholder and mark unavailable visual or hardware gates as pending.

Finish at the Phase 1 milestone with a concise report: files changed, commands to reproduce, checks performed, evidence paths, remaining blockers and the next task. Do not claim facial realism or device performance from a loading smoke test.
```

For later tasks, replace the phase and outputs while keeping the same evidence discipline. If the final goal is only Blender stills or rendered animation, retain the setup and character-review stages, omit browser-specific work, and deliver the approved Blender scene plus renders or animation instead.

## Source basis and verification limits

The plan synthesizes the supplied files: [Browser Rendering Realistic Humans Research](library-file\:libfile_1c55dce6cd6c8191bd930bfd816a7026), [Realistic Humans in Blender Research](library-file\:libfile_66e664eb9a2081919f2d4554dd760003), and [Blender Avatar Agent Toolkit](library-file\:libfile_8bc4fe7acb5081918ee331d637c8b432).

The toolkit supplies setup and repeatability requirements; the Blender research supplies artistic dependencies and visual gates; the browser research supplies runtime contracts and initial budgets. The exact phase grouping, repository layout and first-task prompt are recommendations created for this plan.

Primary documentation was spot-checked for MPFB setup, Babylon scattering, glTF validation and glTF Transform operations. This does not re-audit every version, API, price or asset-license statement in the attachments. No character was built, rendered or benchmarked as part of creating this plan.
