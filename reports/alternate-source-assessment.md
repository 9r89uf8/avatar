# Second-source human-head assessment

Checked 2026-10-03. Scope: an editable Blender source plus model/texture bytes deliverable to a browser, including a possible later commercial app. No account was created, mailing list joined, clickwrap accepted, or restricted asset downloaded. The project master and web model were not changed.

## Result

**No ready-to-use, high-resolution scanned female head with measured skin maps and an unambiguous permissive redistribution grant was established.** Digital Emily 2, Louise, 3D Scan Store, FaceScape and Multiface fail the rights/access requirements. Artec has clearly licensed scans but the relevant complete heads are male and not a female portrait material source.

**Google GNM Head v3.0 is a real, materially different geometry candidate.** Its model data and implementation are expressly Apache-2.0, with an MIT notice for adapted tongue animation meshes. It is scan-derived parametric head anatomy, publicly downloadable without an account. It can be sampled/fitted locally and exported to Blender. It does not supply measured facial albedo, normal, roughness, displacement or scattering maps. A candidate comparison is warranted; immediate replacement of the existing head is not yet justified.

## Acquired candidate: Google GNM Head 3.0

Official sources:

- Model/data grant: https://huggingface.co/google/gnm-v3
- Data download actually completed: https://huggingface.co/google/gnm-v3/resolve/main/v3_0/gnm_head.npz?download=true
- Official code: https://github.com/google/GNM
- Exact code commit: `940c36b850d951f14203e751463bc9b422900fad`
- Full license including MIT tongue component: https://github.com/google/GNM/blob/940c36b850d951f14203e751463bc9b422900fad/LICENSE
- Technical report: https://arxiv.org/html/2607.23687v1

Local: `gnm/gnm_head.npz`, 53,328,601 bytes, SHA-256 `61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb`. This exactly matches Google's published checksum. Full unmodified source checkout: `gnm/source/`.

Measured NPZ contents (loaded with `allow_pickle=False`):

- 17,821 vertices, 17,662 quads / 35,324 triangles
- 253 identity parameters: head, eyeball and teeth shape
- 383 expression parameters with separate eye and lower-face regions, tongue and iris
- Four joints, weights, pose correctives, quad and triangle UVs
- Six components: skin, left eye, right eye, upper teeth/gums, lower teeth/gums, tongue
- Named masks for upper/lower lips, mouth interior, eye sockets, sclera, iris, pupils and facial regions

The core source repository's texture directory contains only `edgeflow_bw_4k.png`, a UV/topology diagnostic. It contains no photographic skin maps. The paper's larger captured-image/scan database is not the released ready-textured product.

Apache-2.0 permits modification and source/object redistribution, including commercial use. Preserve the complete license and applicable copyright/attribution notices, identify modifications, and retain the MIT tongue notice where that component is included. There is no asset-extractability prohibition in this grant. This is a source-license assessment, not a promise that unrelated likeness/publicity rights are covered.

### Actual local test

`gnm/generate_diagnostic.py` loads the official identity decoder's H5 weights and evaluates its exact Dense/ReLU graph with NumPy. It uses a female condition plus an even mixture of the source model's four demographic categories; this is not an inference about the reference person's ethnicity. No age selector exists, so female sampling alone does not certify a requested age. The samples shown are only anatomical candidates.

- `gnm/diagnostic_meshes.npz`: template, female class-center and deterministic sample 42 with the original quad UV data
- `gnm/gnm-clay-diagnostic.png`: rendered, visually inspected neutral clay comparison
- `gnm/gnm-diagnostic.blend`: editable isolated diagnostic scene
- `gnm/render_diagnostic.py`: repeatable Blender import/material/render script

The neutral-pose mesh formula used here is template + identity basis × coefficients. Use the official forward implementation for nonzero expression/pose/rig output. The diagnostic removes corneal faces to expose the iris and adds one subdivision level for display. It is not a finished optical-eye material or a shipping character.

The visible lid-to-eye fit, nostril forms and closed-lip contour are promising. The result is still a smooth generic head. There is not enough evidence to claim better reference likeness than the current model; comparing a clay source to a textured finished avatar is not a controlled final-quality A/B.

### Reference fitting without uploads

The first-party browser implementation includes a local MediaPipe fit path. I executed its dependency-free `FaceFit.js` in Node using the project's existing local 478-point reference landmark JSON, with the unquantized GNM basis and unit component scales. No reference photo was sent to a service.

- `gnm/fit_existing_landmarks.mjs`: reproducible fitting script
- `gnm/local_reference_fits.json`: fitted identity vectors and caveats
- `gnm/reference_fit_meshes.npz`: resulting neutral meshes
- `gnm/gnm-reference-fit-diagnostic.png` and `.blend`: template versus the frontal-reference identity fit, front and 25-degree view

Frontal `8acb...`: 166 points, 24 identity components, residual 1.920 → 1.266 mm in model-aligned landmark space. Side `j1wm...`: 5.101 → 4.436 mm. **These are residuals to estimated landmarks, not a measured reconstruction error or likeness score.** The existing landmarks use legacy MediaPipe FaceMesh, while the browser mapping was calibrated for FaceLandmarker, so this is a practical-path test rather than a certified fit. The solver deliberately excludes highly expression-dependent mouth/eye points from identity fitting, and the automatic fit needs visual refinement for the reference's lips/eyelids.

### First-party browser implementation

- Live: https://xrblocks.github.io/docs/samples/GNM-Head/
- Current source: https://github.com/google/xrblocks/tree/main/samples/avatar_lab/gnm/
- Source snapshot commit checked: `c737bdfd0968777dcd3a2c8e213d71340b951fa1`
- The GNM README's older `demos/gnm` source link now gives 404.
- Relevant source files and root license saved under `gnm/browser-source/`.

The live page loaded and displayed Female sampling, Fit, Identity, Expression, Pose, Animate, View and Save controls in the cloud browser. It reported failure creating the WebGL renderer context, so live rendering was not verified there. Node fitting and Blender rendering were actually run instead.

Source inspection confirms: a chosen image File/Blob is decoded with `createImageBitmap`; landmark inference runs through client-side MediaPipe; only runtime/model downloads are needed by this fit path. No image-upload endpoint is present in these fitting modules. The separate optional texture-synthesis utility calls Gemini with a reference photo and is not this local fitting path. It was not used. The browser's lone textured-head example is AI-generated Mona Lisa albedo, not a contemporary female skin scan.

The browser source has OBJ export and JSON parameter presets. For editable Blender creation, importing native NPZ quads/UVs directly preserves better structure than a screenshot or rendered proxy. Converting a selected, fitted pose into glTF is straightforward; preserving the full statistical parameter interface in Blender or glTF is additional implementation work.

### Integration costs and decision gate

GNM is a new head topology and UV layout. Existing MPFB face morphs, fitted eyebrow/lash attachments, skin UV sheets and neck seam cannot be assumed compatible. A switch means fitting a head, remapping/baking the reference color, rebuilding contact/attachment geometry and deliberately transferring animation. The body and groom can remain sources, but are not automatically drop-in compatible.

Recommended next gate: a head-only, same-camera/same-light A/B using a locally refined GNM fit and the existing reference projection. Inspect eyelid thickness/contact, mouth corners and lip seal, nose silhouette and jaw profile before touching the master. If it cannot improve those with comparable material treatment, stop the branch. More shader tuning does not substitute for missing measured skin material channels.

## Acquired alternative: Blender Human Base Meshes 1.4.1

- Official license/listing: https://www.blender.org/download/demo-files/
- Direct archive: https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip
- Local: `blender-base-meshes/`; 50,643,039-byte archive
- SHA-256 `811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515`
- Actual Blender inventory: `blender-base-meshes/inventory.json`

Official listing, embedded bundle README and relevant asset metadata say CC0. The bundle calls Dan Ulrich's realistic head assets scan-data models with multiresolution details. The sculpting head has 3,307 base vertices / 3,300 polygons; animation head 3,242 / 3,234. The realistic female body's base has 10,582 vertices / 10,590 polygons, with separate eyes. There are no image textures in the file (only an empty Render Result), and the realistic head/body mesh slots have no materials. These are useful anatomy/sculpting bases, not complete scanned skin assets. A stale standalone text block refers to the unrelated Rain rig's CC-BY; preserve it, but the specific bundle README and relevant asset license fields state CC0.

## Excluded sources

### Digital Emily 2 / USC Wikihuman

Official: https://vgl.ict.usc.edu/Data/DigitalEmily2/

The page supplies OBJ/Alembic, diffuse, specular, single-scatter, displacement, mask and micro-displacement assets. This is the correct technical class of material capture for a realism upgrade. However, its notice limits image use to research/illustration, excludes commercial use and forbids transfer/redistribution. No explicit broader model/data redistribution grant was found. The wording refers to images; that ambiguity is not a permissive model grant. A derivative GitHub repository's MIT license does not relicense USC's underlying model/textures. Not downloaded or used. The official page's OBJ/maps anchors remain the authoritative download entry points; no restricted files were retrieved.

### Eisko Louise

Official: https://eisko.com/louise/

High-quality rigged female digital double in Maya with textures. Its page explicitly applies CC BY-NC-ND 4.0 and additionally says not to alter the head/rig or share/distribute it. The download requires a form. Fails commercial use, editable derivatives and model-byte distribution. Not downloaded.

### 3D Scan Store free female

Official: https://www.3dscanstore.com/free-female-download
Terms: https://www.3dscanstore.com/terms-and-conditions-licensing

Already excluded in `reports/source-selection.md`: email/mailing-list gate plus restrictions on free commercial use and scan redistribution. No fresh download attempted and no assumption that rendered-work rights permit raw browser delivery.

### FaceScape / Multiface

- https://github.com/zhuhao-nju/facescape
- https://nju-3dv.github.io/projects/FaceScape/static/license/LicenseAgreement_FaceScape.pdf
- https://github.com/facebookresearch/multiface

FaceScape offers detailed geometry and 4K displacement/texture maps, but its data license restricts use to noncommercial research, forbids distribution and limits application eligibility. Multiface expressly uses CC BY-NC 4.0; it is multi-view appearance research data, not a permissive app-asset license. Neither was downloaded.

### Artec scans

Official Head: https://www.artec3d.com/3d-models/head
Verified direct OBJ URL: https://cdn.artec3d.com/content-hub-3dmodels/man_bust_obj.zip?VersionId=1N60ZswVFe5Bmp4zFOXRqJ_TJsEypvfr
Official Face: https://www.artec3d.com/3d-models/face
Official Eye: https://www.artec3d.com/3d-models/eye

Artec links CC BY 4.0, which supports modification/redistribution/commercial use with attribution and change notices. The relevant whole-head sources are male (`man_bust` and a page explicitly describing a male head). The eye scan is only a small patch, useful for anatomical observation rather than a female face replacement. No complete high-quality female scan was found in the reviewed gallery. These do not close the current source gap; no extra geometry was downloaded.
