# Viewer verification

Updated 2026-10-03. Code and asset-contract checks pass. Live WebGL rendering, appearance, and the diagnostic download UI remain unverified in this cloud environment.

## Current asset validation

Latest verified production GLB:

- SHA-256: `d310f41100d5ef98d1691a6678795f23c76073cc92da30bc888cbb452edc4b60`
- Size: 30,248,948 bytes
- Khronos validator: zero errors, 14 reviewed skinned-mesh hierarchy warnings
- Sidecar hash, material/node/morph bindings and eight-weight contract: no issues
- Maximum nonzero weights: eight on body, tee, collar and trousers; two or three on groom cards
- Required eye/head controls, hair bones and facial morphs are present

The authoritative full inventory is `../reports/gltf-validation.json`; summaries are `asset-validation-summary.txt` and `render-contract.txt`. Run `npm run verify:asset` and `npm run verify:contract` after any subsequent export. Earlier asset summaries are superseded by the exact hash above.

## Passed code checks

- Strict TypeScript check and production build (Vite 7.1.9, TypeScript 5.9.3, Babylon.js 8.32.0).
- **30 tests pass.** Coverage includes motion bounds/timing, microgaze continuity, numerical aggregation, repeated capture, reset/dispose/cancellation cleanup, bounded state history, terminal stalls, malformed input, weight counting and runtime skinning invariants.
- Supplied tracked Windows rolldown files remain unchanged.
- No model, poster or Blender source was edited by this diagnostic-hardening work.

Commands and current logs: `npm run typecheck` → `typecheck.txt`; `npm test` → `unit-tests.txt`; `npm run build` → `build.txt`.

## Runtime skinning contract

Before loading, both runtime and CLI reject `JOINTS_2` / `WEIGHTS_2` or higher instead of silently truncating beyond the installed loader's supported influences. Per-primitive nonzero weight counts support embedded float/normalized-integer, interleaved and sparse accessors.

After import, the viewer resolves each relevant mesh/instance through the pinned Babylon loader's exact glTF JSON-pointer metadata. A delivered primitive requiring more than four nonzero weights must have all of:

- Actual `numBoneInfluencers >= 8`
- `mesh.isVerticesDataPresent(VertexBuffer.MatricesIndicesExtraKind) === true`
- `mesh.isVerticesDataPresent(VertexBuffer.MatricesWeightsExtraKind) === true`

A missing mapping, truncated mode, missing buffer or unverified buffer presence produces a clear load error. Diagnostics retain the observed mode and both buffer-presence results. This establishes a CPU-side loader invariant only; it does not claim successful shader/GPU execution or deformation quality.

## Local-only diagnostics and failure handling

Scene details offers a user-triggered ten-second capture. It creates/downloads JSON locally without telemetry, uploads or additional diagnostic network requests. It records browser-reported renderer/capabilities, measured asset SHA, primitive and runtime bone-influence data, skeleton/bone/mesh/triangle counts, camera, viewport, quality and effective rendering options.

Paused, idle, blink, smile, head turn, orbit, microgaze, hair and skin-diffusion settings, reduced-motion preference and a bounded settings timeline are explicit. Paused animation still renders frames. Interval-average FPS, median/p95/p99 frame times and draw calls are descriptive observations without an invented performance budget. Whole-observation throughput, trailing frame gap and timer overrun are separate, so a terminal stall is not hidden. The open details panel and instrumentation may affect timing; these are not isolated GPU timings, cold-load measurements or device certification.

Cancel, closing details, hiding the tab, reset, context loss and disposal terminate sampling with an explicit reason. Timer and sample cleanup are unit-tested. Renderer integration removes owned observers/listeners and aborts pending asset fetches on disposal. Download object URLs are revoked when replaced or on page exit.

Unsupported WebGL or loading failure preserves the existing explicitly labeled still poster, disables unavailable live controls and offers a local readiness report. Missing renderer information and measurements remain null; no live FPS or rendering success is inferred.

## Material treatment: compiled, not visually approved

Exact `GroomDarkBrownCards` uses alpha testing at .32 while preserving authored roughness/specular/anisotropy, with MSAA/FXAA and specular antialiasing. Exact `CorneaOptical` is excluded from casting/receiving shadows; `EyeSurface` retains lid shadows. Skin diffusion applies only to the exact mapped skin material. Compilation is not appearance approval.

## Verified cloud-browser graphics blocker

On 2026-10-03 the permitted CUA cloud Chrome was checked read-only against the official Khronos pages:

- https://get.webgl.org/: visible `webgl-disabled` result, WebGL disabled or unavailable; no cube
- https://get.webgl.org/webgl2/: visible `webgl-disabled` result, WebGL2 disabled or unavailable; no cube

Actual screenshots were captured in CUA output. No renderer/vendor was exposed by the failed pages. The structured evidence is `browser-capabilities.json`. No browser flags, security settings or configuration were changed. Private hosting alone would not establish the required graphics capability.

### Historical preview-infrastructure checks

Loopback was rejected by the cloud browser with `ERR_BLOCKED_BY_CLIENT`. The documented internal `terminal.local:4173` route returned `502 Connection refused`; retained local servers were unreachable from the separate browser runtime. The documented supervisor was unavailable. Local agent-browser/Chromium required Unix sockets denied by the execution environment, including the reviewed escalation attempt. Test servers were stopped; nothing was deployed. No new browser or workaround attempts were made during this hardening task.

## Remaining verification

Use a supported, authorized environment that can create WebGL2 contexts to verify the live avatar, diagnostic capture/download, camera views, blink contact, expressions, head/eye motion, hair, lighting/quality changes, pause/resume/reset, repeated loading and mobile layout. Capture real screenshots and inspect console/WebGL errors. Successful software rendering would establish loading/interactions only; target-device performance and human photorealism approval remain separate gates.
