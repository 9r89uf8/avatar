# Adult avatar studio

An editable adult female character built in Blender, an uncompressed rigged GLB, and a TypeScript/Babylon.js inspection viewer. The supplied image references guide appearance; the character is real anatomical mesh geometry with a body rig, facial morph targets and head-driven hair.

Current status: technically validated source/export checkpoint and tested viewer code. The current procedural refinement has reached diminishing visual returns. Do not treat this as approved photorealism or measured target-device performance. See docs/progress.md and reports/visual-iteration-log.md for the current evidence and unresolved gates.

## Verified work-in-progress delivery

This branch preserves the 3 October 2026 checkpoint for review. The visual target remains unmet: skin, facial structure and hairstyle still read as synthetic. Browser appearance and target-device performance have not been verified.

- Editable Blender source: 68.1 MB, all 12 images packed; restored as `scenes/avatar-master.blend`
- Rigged GLB: 30.2 MB; restored as `exports/avatar-uncompressed.glb` and `web/public/assets/avatar.glb`
- [View the current source portrait](renders/portrait-baseline.png) and [GLB portrait](renders/glb-portrait-refined.png)
- [Quality status and remaining gaps](docs/quality-status.md)
- [Next-source and artist handoff](docs/next-source-handoff.md)
- [Exact delivery hashes](reports/github-delivery-manifest.json)

Clone this branch or use GitHub’s Download ZIP to obtain the viewer, prepared maps, selected pipeline and validation evidence together. Large assets are stored in numbered parts to fit the delivery connection. Restore all nine asset paths once from the repository root:

    python scripts/restore_assets.py

This verifies every part and complete checkpoint hash, then creates the source, GLBs and large prepared maps. It refuses to overwrite a different existing file. Opening the packed source requires Blender; restoration itself uses only Python’s standard library. No Git LFS or paid asset download is needed. The viewer’s normal npm commands automatically restore its GLB using Node, so running the viewer does not require Python.

[The part manifest](config/delivery-parts.json) records exact paths, sizes and hashes. The historical ZIP packages are preserved separately; this branch contains their selected working files without duplicating archive bytes or temporary experiments. Selected historical reports are partial experiment records; some rejected-study files they mention are intentionally omitted. The core build/export/viewer paths and selected evidence are included.

## Files

- scenes/avatar-master.blend: self-contained editable master with packed images and source strand groom
- exports/avatar-uncompressed.glb: browser derivative with skinning, facial morphs and a head-turn clip
- exports/avatar.web.json: exact material, bone, morph and camera contract, bound to the GLB hash
- web/: responsive local browser viewer
- scripts/blender/: deterministic build, surface bake, review, export and inspection scripts
- scripts/reference/: landmark analysis and reference-color preparation
- config/, licenses/, reports/: pinned inputs, permissions, checks and visual evidence

The original research documents, reference images and uploaded Windows rolldown files remain in the repository. The latter are dependency files and are not needed by the Linux/browser build.

## Run the viewer

Requires Node.js 22.18+; Node.js 24.19.0 was used for validation.

    cd web
    npm ci
    npm run dev

Open the local URL printed by Vite. The predev hook restores and verifies the supplied GLB from the repository parts when needed. Controls include orbit/zoom, portrait/three-quarter/full body, lighting, blink, smile, head turn, pause/reset and rendering quality. Reduce motion follows the operating-system preference.

Checks:

    npm test
    npm run verify:contract
    npm run verify:asset
    npm run build

The GLB validator and contract checks do not establish visual quality. The cloud executor's browser bridge was unavailable, and the permitted cloud browser failed official WebGL/WebGL2 capability tests. Real Babylon appearance and hardware frame-rate checks remain explicit pending gates.

## Rebuild the Blender source

Tested with Blender 4.3.2 and MPFB 2.0.17 at the pinned commit in config/source-downloads.json. The installed Cycles build lacks OpenImageDenoise; source renders deliberately disable denoising.

    python scripts/restore_assets.py
    python -m pip install -r scripts/requirements-build.txt
    python scripts/fetch_assets.py
    python scripts/prepare_eye_texture.py
    python scripts/prepare_delivery_textures.py
    BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b --factory-startup --python-exit-code 1 -P scripts/blender/build_character.py
    BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b scenes/avatar-master.blend --python-exit-code 1 -P scripts/blender/inspect_scene.py
    BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b scenes/avatar-master.blend --python-exit-code 1 -P scripts/blender/export_avatar.py

On Windows, set BLENDER_USER_RESOURCES to a project-local directory using PowerShell syntax, and invoke the installed Blender executable. The scripts themselves use portable pathlib paths. Source texture preparation requires Pillow and NumPy. The reference workflow's separately pinned requirements are in scripts/reference/requirements.txt.

The included prepared texture maps make ordinary rebuilding independent of a new detector run. Full source-map regeneration is documented in reports/reference-analysis.md; its calibration hash must match. Surface maps can be recreated with scripts/blender/bake_surface_maps.py. Do not rerun calibration casually after changing the face, camera or UVs.

Review the actual derivative in a fresh process:

    BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b --factory-startup --python-exit-code 1 -P scripts/blender/render_export.py

This produces a Cycles render of the imported GLB, not a browser screenshot. Portrait, profile, three-quarter, full body and facial test renders use render_review.py. Preserve fixed cameras and lighting when comparing revisions.

## Rights and limitations

Selected MakeHuman system/community geometry and original maps are CC0; MPFB tool code is separately GPLv3. The new groom and procedural detail are project-authored. User-reference-derived color retains the provenance of the supplied images. See licenses/ASSET-CREDITS.md and config/assets.json.

This project is for personal use. The licensing inquiry is cancelled. No paid scan library, restricted extractable human asset or account credential is included. Generated pore detail is an approximation, and the reference face contains approximately 338 pixels of horizontal detail; a 4K atlas does not make it a 4K scan. Browser smoothness must be measured on the actual target device.

## Garment export parity

The delivery mesh explicitly supports up to eight joint influences. The pinned Babylon loader consumes JOINTS_0/1 and WEIGHTS_0/1; higher sets are rejected. The exporter corrects garment bind coordinates so subdividing before skinning reproduces the evaluated source surface. Verify after export with:

```sh
BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b scenes/avatar-master.blend --python-exit-code 1 -P scripts/blender/verify_cloth_export.py
```

`reports/cloth-export-parity.json` binds its result to the GLB hash. This is source-versus-GLB geometry verification, not browser GPU or frame-rate evidence.

## Selected eyelid refinement

The current build uses restrained mesh lashes and a warm lid wetline, bound to the same facial morphs and head joint. A targeted UV albedo correction removes photo-derived dark streaks that stretched during blink. It is authored color, not measured skin data; neutral and closed-lid images are documented in reports/lid-diffuse-experiment. The original lash asset and reference maps remain preserved.

A clean-extraction, no-render source rebuild was checked using the already-verified pinned vendor cache. Its object, bone and morph inventory matches this checkpoint. This did not repeat network downloads or certify byte-identical .blend serialization; see reports/fresh-archive-rebuild.json.
