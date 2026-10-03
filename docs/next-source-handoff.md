# Candid status and substantive next step

## What this checkpoint is

An editable clothed adult full-body avatar, a portable skinned GLB, an inspection viewer, and a reproducible source pipeline. Specific geometry/export/deformation bugs are fixed and verified. It is not an ultrarealistic character, and no human appearance approval has been obtained. Passing code and mesh tests does not change that assessment.

The current autonomous procedural approach has reached diminishing visual returns. Further small noise, shader, proportion and strand-count adjustments are not a credible plan for reaching the requested perceptual target with this source. Blender supports additional sculpting and grooming here; this is not a blanket inability to edit 3D. The limitation is the quality of the supplied/generated starting data and the demonstrated results of this approach.

## Remaining visible gaps

- Generic/smooth face planes and low-information skin. The original reference face spans about 338 pixels; generated, uncalibrated views do not supply scan-quality shape, pore/displacement or roughness.
- Clean blink surfaces now avoid stretched photo-derived lash marks, but neutral eyes look bare/doll-like. The lid shape, lash density/direction and iris/cornea treatment need coordinated character-art work.
- The root incision is removed and roots are surface-fitted, but the hairstyle still has a hard frontal boundary, regular clumps/flow and card sheen. It needs a deliberately sculpted/groomed silhouette and density, not just more strands.
- Reference-derived color retains some baked illumination and brow/face information. It is not measured, fully delit albedo.
- Real Babylon output and device smoothness remain unverified. The permitted cloud browser fails official WebGL and WebGL2 capability pages; publishing elsewhere alone would not fix that browser's capability.

## Personal-use scope and possible future input

On 2026-10-03 the user confirmed this project is for personal use, cancelled the proposed licensing inquiry, and reiterated approval for the GitHub branch delivery. Continue with the current verified assets. No vendor inquiry or paid-source acquisition is pending.

A possible future quality upgrade would use a high-resolution female head/material source permitted for the intended personal-use workflow, followed by a substantive face/groom art pass and verification on a WebGL2-capable target device. Useful inputs would include a retopologised editable head, matched UVs, neutral delit color, normal/displacement and roughness/specular data. A higher-resolution beauty portrait alone does not supply those missing channels. No replacement asset is selected for this delivery.

A previously researched candidate was 3D Scan Store **HD Female Head Model 01**: https://www.3dscanstore.com/hd-head-scans/hd-head-models/hd-female-head-model-01 . On 2026-10-03 the listed personal price was £69.99 and the single-project commercial total £369.98 before unverified checkout taxes. It supplies a retopologised UV head, Blender scene, OBJ/FBX, very high-resolution sculpt and 16K maps/16-bit displacement. Its current terms restrict viewers, software bundling and standalone derivatives, so a standard purchase cannot be assumed to permit this delivery: https://www.3dscanstore.com/terms-and-conditions-licensing . No purchase or vendor contact has been made.

The proposed vendor inquiry is cancelled. Commercial deployment is not the user's goal, and no new permission or purchase request is part of the current delivery. Personal-use intent does not establish unverified rights in a new third-party asset; the existing verified assets remain selected. Historical procurement findings and the Reallusion alternative's export restrictions are retained in reports/asset-procurement-options.md.

## Artist handoff

- `AvatarBody` keeps its modeling and facial keys. New anatomy requires expression and eyelid refitting, not just a neutral-image comparison.
- `LashesNatural` and `LidWetline` are ordinary skinned/morphed meshes. The original `Lashes` remains hidden/excluded; original reference maps also remain available for comparison.
- The strand groom is driven by the editable `HairGuidePoints.*` meshes through Geometry Nodes. Native curves and browser cards are separate representations. Editing only the rendered curves may be overridden by their guide modifier; keep guide/card correspondence and skin weights consistent.
- Rebuild the lid attachments and surface-root groom after changing head anatomy. Recheck neutral, three-quarter, profile, full blink, smile and head-turn combinations.
- Preserve the eight-weight viewer invariant and source/GLB garment parity. Read current reports rather than assuming any old hash or screenshot applies to a revised model.

On an authorized WebGL2 device, use the viewer's local ten-second diagnostic capture and provide actual screenshots. Reports stay local and do not transmit telemetry. That can establish measured behavior; user approval of the visual target remains a separate gate.
