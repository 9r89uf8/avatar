# Atelier avatar viewer

A small TypeScript + Babylon.js viewer for the project-owned GLB. It is designed to render real geometry in WebGL 2. If graphics or loading fails, a clearly labeled still render is shown with disabled live controls and a readiness report.

## Run

Node.js 22.18+ recommended (Node 24 used here). From `web/`:

```sh
npm ci
npm run dev
```

The GitHub delivery stores large binaries as verified parts. `npm run dev`,
`npm run build`, `npm run verify:asset`, and `npm run verify:contract` automatically
restore `public/assets/avatar.glb` using Node.js built-ins; Python and Git LFS are
not needed to run the viewer. `npm run restore:assets` also runs this step directly.
Restoration checks every part and the combined SHA-256, publishes only a complete
file, and refuses to overwrite a different existing GLB. Keep `../config/` and
`../delivery/` beside `web/` when using the repository delivery. Older standalone
browser ZIPs without the delivery manifest already contain their GLB, so the step
safely does nothing there.

To restore the editable Blender source, prepared maps, and export copy after
cloning, run `python scripts/restore_assets.py` from the repository root (Python
3.9+; standard library only). Optional repository-relative paths select individual
assets, for example `python scripts/restore_assets.py scenes/avatar-master.blend`.
Add `--verify-only` to check parts, combined hashes, and any existing target files
without writing assets. A changed local asset is deliberately preserved; move it
aside yourself if you want to restore the delivery version. Whole-asset aliases
share the same source bytes and do not depend on restoration order.

Open the local address printed by Vite. For a development machine on which a different bind address is needed, use `npm run dev -- --host 0.0.0.0`. The default loopback bind also works in constrained execution environments where network-interface enumeration is unavailable.

```sh
npm run typecheck
npm test
npm run verify:asset
npm run build
npm run preview
```

`verify:asset` runs the official Khronos validator, checks GLB SHA-256 against the sidecar, and verifies exact material/node/morph bindings. It writes `../reports/gltf-validation.json`. Warnings must be reviewed; a zero-error validator result alone is not a visual-quality approval.

## Controls

- Drag the actual 3D viewport to orbit; scroll/pinch to zoom; Shift + drag to pan.
- Portrait / three-quarter / full-body frame the asset at preset distances.
- Smile and head turn are bounded. Blink, idle and binocular microgaze use a shared deterministic simulation clock. Microgaze stays within ±2° yaw / ±1° pitch, with eased transitions and long holds. Exact eye-bone local Z yaw and local X pitch preserve the iris orientation.
- Pause freezes animation, while camera inspection remains available. Reset restores neutral expression, portrait camera, studio lighting and high quality.
- Hair secondary motion runs on exact mapped skeleton nodes, using a substepped damped spring driven by head angular velocity.
- Studio, daylight and rim-light presets are real PBR lighting changes.
- Skin diffusion affects only exact sidecar skin-material names. Balanced quality disables the expensive diffusion pass.
- Keyboard: 1/2/3 change view; Space pauses; R resets. Reduced-motion preference begins paused.

## Asset contract

`public/assets/avatar.web.json` uses `schemaVersion: 1` and references `avatar.glb` through `modelUrl`. `glbSha256` (or `modelSha256`) is verified on load when provided. The loader also verifies WebGL 2 availability and shows an actionable loading/retry state on failure.

Semantic bindings are exact, case-sensitive names:

- `skinMaterials`, `eyeMaterials`, `hairMaterials`: material-name arrays. The skin list controls shader overrides; imported eye/hair materials are otherwise preserved.
- `headNode`: the skeleton's linked transform node.
- `hairNodes`: the HairRoot/Mid/Tip bone nodes to animate. Local rest quaternions are preserved.
- `morphTargets.blink`, `.smile`, optional `.breath`: arrays of target names.
- `hair.alphaCutOff`: optional strand cutout threshold (default .32). Only exact `GroomDarkBrownCards` receives the alpha-test override; authored roughness, specular and anisotropy stay intact. High-quality MSAA and FXAA provide antialiasing. Hardware alpha-to-coverage is not claimed.
- `nonShadowMaterials`: exact materials to omit from casting and receiving shadows. Defaults to the verified `CorneaOptical` shell, so the cornea does not falsely blacken its iris while the opaque globe still receives lid shadows.
- `metersPerUnit`: scene-unit calibration for diffusion; default 1.
- `cameras.portrait`, `.threeQuarter`, `.full`: `{target:[x,y,z],radius,alpha,beta}` in right-handed glTF coordinates and radians.
- Optional `skin`: `{roughness,specularIntensity,diffusion:[r,g,b],thicknessMillimeters}`. Albedo, normal and texture maps stay imported from the GLB.

Camera presets are inferred from actual mesh bounds if absent. Missing bindings are listed in Scene details rather than silently guessed. The app never pretends a missing expression works.

The generated studio IBL is locally owned, linear HDR data with diffuse spherical harmonics and a GGX roughness-prefiltered cube. No remote environment or texture URL is required. ACES tone mapping, MSAA/FXAA and moderate sharpening are used; depth-of-field and bloom are deliberately off so anatomical and shading defects remain visible.

## Integration API

`window.avatarViewer` exposes the live viewer for embedding and reproducible diagnostics:

- `ready`: resolves after GLB loading/binding.
- `setView(view, animate?)`, `setLighting(preset)`, `setQuality('high'|'balanced')`.
- `setScattering(enabled)`, `blink()`, `pause(paused)`, `reset()`, `dispose()`.
- `state` contains manual expression, head turn, idle, blink, hair and orbit settings.
- `getInventory()` returns the loaded mesh/material/morph/node inventory and binding warnings.

Pause freezes the simulation clock. Manually changing expression values while paused applies when movement resumes. Resource ownership is per viewer, and retry disposes the prior renderer/scene.

## Scope of verification

The numerical tests cover blink bounds/contact/timing, frame-independent damping, clamping and camera-bound inference. Production compilation is separate from browser QA. A software-rendered browser check is evidence of loading and interactions, not a real-device performance or photorealism approval. Consult the project reports for the actual verification performed.

The original tracked Windows `@rolldown` binaries were preserved unchanged. Local development dependencies were installed separately in this restricted environment and symlinked without removing those supplied files; a normal fresh checkout can use `npm ci`.


## User-triggered local diagnostics

Open **Scene details → Capture 10 seconds** after the real GLB loads. The viewer observes completed browser render callbacks for a bounded ten-second window, prepares a JSON Blob locally, and requests a local download. **Save JSON** remains available if the browser does not start that download. No diagnostic telemetry, upload, fetch, beacon, or additional network request is made.

The report includes:

- Browser-reported WebGL renderer/vendor/version and actual engine capability limits. These values may describe masked, virtual or software rendering; they are not asserted to identify physical hardware.
- Initial/final camera, viewport CSS/render resolution, pixel ratio, quality and effective MSAA/FXAA/skin-diffusion state.
- The SHA-256 computed from the loaded GLB bytes, expected sidecar hash, verification result, byte count, mesh/triangle/material/skeleton/bone counts, actual per-mesh `numBoneInfluencers`, and per-primitive maximum/mean nonzero weight counts.
- Raw render-callback intervals, observed average FPS, median/95th/99th percentile frame times and draw-call distributions. These are descriptive observations, not a pass/fail budget, isolated GPU timings, cold-load benchmark or photorealism approval.
- Paused, idle, blink, smile, head turn, orbit, hair-motion and skin-diffusion settings; reduced-motion preference; effective microgaze and hair activity; and a bounded timeline of settings/viewport changes. Pausing animation does not stop scene rendering, and is explicitly recorded.

Cancel, closing Scene details, hiding the tab, a reset, graphics-context loss or viewer disposal cancels the sample with an explicit reason. Timers, retained samples, scene observers, visibility listeners and local download URLs are cleaned up by their owners. Cancelled/empty samples do not invent a frame rate. If WebGL or loading fails, the still-render fallback stays visibly labeled, live controls are disabled, and **Save readiness report** downloads only the actual failure/browser information. Missing renderer/measurements remain null.

The installed Babylon loader consumes only weight sets 0 and 1. Both the runtime loader and verification scripts now reject `JOINTS_2` / `WEIGHTS_2` or any higher set instead of silently dropping influences. Counting supports embedded float or normalized-integer, interleaved and sparse weight accessors.

`npm test` covers percentile aggregation, real-interval FPS arithmetic, unknown counters, bounded settings history, cancellation/reset/dispose and repeat captures, plus four/eight-weight counting and higher-set rejection. These tests do not replace an actual local browser download/render check; this cloud browser still cannot create WebGL contexts.

After import, a separate runtime invariant resolves the pinned loader's exact glTF JSON-pointer metadata for each relevant mesh/instance. A source primitive requiring more than four nonzero weights must have actual Babylon `numBoneInfluencers >= 8` and both extra joint/weight vertex buffers present; missing pointer mappings or truncated runtime configuration stop loading with an explicit error. Diagnostics include the source requirement, observed runtime value and the result. This is CPU-side loader-configuration evidence, not a successful GPU/shader execution or deformation-quality claim.

The report distinguishes interval-average FPS from whole-observation frame throughput. It also records the gap after the final frame and any delayed timer completion, so a terminal browser stall cannot be hidden behind otherwise fast sampled intervals.
