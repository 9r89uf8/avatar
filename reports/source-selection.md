# Character source selection and verified loading

Checked 2026-10-03. This report covers source assets and a disposable API smoke test, not approval of portrait likeness or realism.

## Decision

Use the official **MPFB 2.0.17 / MakeHuman hm08 base mesh**, with selected MakeHuman system assets. It provides editable full-body anatomy, shared UVs, modeling targets, automatic asset fitting, body/facial skeleton options, and freely redistributable output. The selected core assets have explicit **CC0** grants, including model and texture bytes delivered to a browser. The MPFB Python application is GPLv3; that code license does not apply to exported model output. Keep those distinctions in the project credits and distribution manifest.

- Official source: https://github.com/makehumancommunity/mpfb2
- Pinned checkout: `vendor/mpfb2`, commit `afb9f530a7c2741dedb8df0ebae2e0b183caec21`
- Official licensing: https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.md
- Local source-license copies: `vendor/mpfb2/LICENSE.md`, `LICENSE.ASSETS.md`, `LICENSE.CODE.md`
- Official pack inventory: https://static.makehumancommunity.org/assets/assetpacks.html
- Exact download URLs, byte counts, archive SHA-256 values and pack metadata paths: `vendor/source-manifest.json`

The source is a genuine anatomically modeled topology, not assembled spheres or a procedural placeholder head. It is a reliable starting point, not an already ultrarealistic portrait asset. Likeness fitting, better skin shading/microdetail, eye optics and hairline refinement remain necessary.

## Materialized assets

Eight official packs have been downloaded and extracted successfully. Archives occupy about 644 MiB in `vendor/downloads`; extracted assets occupy about 717 MiB in `vendor/assets`. Keep raw vendor files outside the web public directory. Do not accidentally commit the whole download cache or nested source Git repository.

| Pack | Scope | Verified source |
|---|---|---|
| makehuman_system_assets | Skin, eyes, mouth parts, stock hair, clothes | https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html |
| skins01 | Natural female skin variants | https://static.makehumancommunity.org/assets/assetpacks/skins01.html |
| eyebrows01 | Mindfront individual-strand brows | https://static.makehumancommunity.org/assets/assetpacks/eyebrows01.html |
| eyelashes01 | Mindfront individual-strand lashes | https://static.makehumancommunity.org/assets/assetpacks/eyelashes01.html |
| faceunits01 | ARKit-named facial targets by Mika Suominen | https://static.makehumancommunity.org/assets/assetpacks/faceunits01.html |
| shirts01 | Female tee and other tops | https://static.makehumancommunity.org/assets/assetpacks/shirts01.html |
| pants01 | Cargo pants, shorts and other trousers | https://static.makehumancommunity.org/assets/assetpacks/pants01.html |
| hair01 | Additional hair alternatives | https://static.makehumancommunity.org/assets/assetpacks/hair01.html |

Every pack is listed by the official inventory as CC0. Selected shipping candidates were checked against embedded headers as well; two inconsistencies are explicitly excluded below.

## Recommended exact files

All paths in this section are relative to `vendor/assets/`.

### Body and skin

- Create body with `HumanService.create_human`, rather than directly importing the neutral base OBJ and trying to infer female deformation.
- Recommended baseline skin: `skins/young_caucasian_female2/young_caucasian_female2.mhmat`.
- Associated image: `skins/young_caucasian_female2/young_lightskinned_female_diffuse2.png`, **2048 × 2048 RGB**.
- Alternative baseline: `skins/young_caucasian_female/young_caucasian_female.mhmat`.
- Both have explicit September 2020 CC0 release headers.
- **No acquired skin image exceeds 2048 × 2048.** This was checked with Pillow across all downloaded skin files. These are full-body UV sheets, so effective face pixel density is substantially below a dedicated 2K face map. They do not constitute 4K source skin, and simply resizing will not recover scan detail.
- `MAKESKIN` makes an inspectable simple material; `ENHANCED_SSS` or `LAYERED` can improve the Blender master but will require deliberate baking or recreation for glTF/browser rendering. Do not assume Blender shader groups or SSS transport automatically export.

### Eyes

- `eyes/high-poly/high-poly.mhclo` creates **1,064 vertices** in the two-eye mesh before subdivision.
- It references `eyes/materials/brown.mhmat` by default, matching the reference eye color.
- `eyes/materials/brown_eye.png` is **1024 × 1024 RGBA**.
- Geometry/material header explicitly grants CC0.
- Separate sclera/iris/cornea optical treatment and tearline contact are still portrait work; the stock material alone does not prove close-up realism.

### Hair

- `hair/long01/long01.mhclo`: **3,239 vertices, 2,054 polygons** before subdivision.
- `hair/long01/long01_diffuse.png`: **2048 × 2048 RGBA**.
- Thumbnail inspected: long straight brown hair with a side/near-center part, broadly useful for the reference silhouette.
- Explicit 2020 CC0 header. This is the safest immediate choice.
- It is alpha-card hair, not strand groom output. Check alpha blending/masking, two-sided rendering, card sorting and scalp gaps in the browser. Add finer silhouette strands only after the base hairline is convincing.

### Clothing

- `clothes/joepal_crude_t-shirt_female/joepal_crude_t-shirt_female.mhclo`: fitted crew-neck short-sleeve shirt, **1,095 vertices, 1,034 polygons**, explicit CC0 header by Joel Palmius.
- Material filename inside the folder is **`crudefemaletshirt.mhmat`**, not the asset folder name. It uses `CrudeFemaleTshirtDiffuse.png`.
- Recolor to charcoal. The source topology is useful, but neckline thickness and natural folds need review.
- `clothes/female_casualsuit01/female_casualsuit01.mhclo` contains a tee and jeans in one asset. It has 2048-square diffuse, AO and normal images and explicit system-asset CC0 release text. If using only its jeans, separate by mesh islands/region in the Blender build, not by guessing that it is trousers-only.

### Brows and lashes

- `eyebrows/mindfront_eyebrows_04/mindfront_eyebrows_04.mhclo`: **20,130 vertices, 14,814 polygons**.
- `eyelashes/mindfront_eyelashes_02/mindfront_eyelashes_02.mhclo`: **16,992 vertices, 12,744 polygons**.
- Both embedded headers explicitly state CC0 and credit Mindfront (Sweden).
- They are high-detail geometry suitable for a source portrait, but expensive relative to the body and already visually smooth as strands. Avoid blindly applying another subdivision level in the web copy. The system `eyebrow*.mhclo` and `eyelashes*.mhclo` assets are lighter alternatives.

### Facial motion

- `targets/faceunits/eyeBlinkLeft.target`, `eyeBlinkRight.target`, `mouthSmileLeft.target`, `mouthSmileRight.target`, `jawOpen.target` successfully load as named shape keys on the MPFB body.
- Pack metadata `packs/faceunits01.json` records Mika Suominen and CC0.
- These are additive target deltas in the original MakeHuman topology. Preserve vertex correspondence. Load before destructive topology edits. Their successful loading is not proof of eyelid closure or lip contact on a modified face.
- Dependent eyelashes/brows need corresponding deformation transfer or facial rigging. A shape key on the body does not by itself animate a separate mesh.

## Actual Blender 4.3.2 test

Executable: `/usr/bin/blender`, version 4.3.2. MPFB manifest supports Blender 4.2.0 and later. No unrecognized installer was executed. Official MPFB source was loaded only into a disposable background Blender process, with writable user resource paths redirected under `vendor/`.

Run:

```bash
BLENDER_USER_RESOURCES="$PWD/vendor/blender-user" \
  blender -b --factory-startup --python-exit-code 1 \
  -P vendor/test_load_mpfb.py
```

Artifacts:

- Runnable source/API smoke test: `vendor/test_load_mpfb.py`
- Execution log: `vendor/mpfb-smoke-test.log`
- Numeric inventory: `vendor/mpfb-smoke-test.json`

Verified successful actions:

1. Register the official extension source in a temporary `bl_ext.avatar.mpfb` namespace.
2. Create a neutral adult female with helper mesh masked.
3. Create the built-in `default` skeleton with **163 bones**.
4. Apply the selected skin and fit high-poly brown eyes.
5. Fit long01 hair, female tee, Mindfront brows and lashes.
6. Load named blink, smile and jaw-open targets.

The body source has **19,158 vertices / 18,486 polygons including helper geometry**. The masked mesh's measured standing height is about **1.606 m** with default height settings and scale=0.1. Helper vertices must not leak into the delivery copy. No master `.blend` was written or altered by this test.

## Practical API recipe

Use the bootstrap at the top of `vendor/test_load_mpfb.py` when running from the vendor checkout. Importing plain `mpfb` is insufficient in current extension versions, because `bpy.utils.extension_path_user` expects an extension namespace.

```python
from bl_ext.avatar.mpfb.services.humanservice import HumanService
from bl_ext.avatar.mpfb.services.targetservice import TargetService

macro = TargetService.get_default_macro_info_dict()
macro.update(gender=0.0, age=0.5)
macro['race'] = {'caucasian': 1.0, 'asian': 0.0, 'african': 0.0}
body = HumanService.create_human(scale=0.1, macro_detail_dict=macro)
# Apply likeness modeling targets before fitting accessories and finalizing the rig.
TargetService.load_target(body, str(target_root / 'nose/nose-scale-horiz-decr.target.gz'), weight=0.2)
rig = HumanService.add_builtin_rig(body, 'default')
HumanService.set_character_skin(str(asset_root / 'skins/young_caucasian_female2/young_caucasian_female2.mhmat'), body, skin_type='MAKESKIN')
eyes = HumanService.add_mhclo_asset(str(asset_root / 'eyes/high-poly/high-poly.mhclo'), body, asset_type='Eyes', subdiv_levels=1)
hair = HumanService.add_mhclo_asset(str(asset_root / 'hair/long01/long01.mhclo'), body, asset_type='Hair', subdiv_levels=0)
blink = TargetService.load_target(body, str(asset_root / 'targets/faceunits/eyeBlinkLeft.target'), name='eyeBlinkLeft', weight=0.0)
```

Here `race` is the source tool's existing target-family selector, not a claim about the person depicted in the reference. Tune geometry by visual comparison, not ethnicity inference.

**Important correction to upstream sample:** `script_samples/01_create_a_basic_human.py` labels a gender=1 character as female. Actual property metadata and macro interpolation establish **0.0 female, 1.0 male**. It also sets every ancestry-family weight to zero in that example. Use normalized weights, and do not copy that sample literally.

Modeling targets are under `vendor/mpfb2/src/mpfb/data/targets/`. Useful categories include `head`, `nose`, `mouth`, `chin`, `jaw`, `eyes`, `eyebrows`, `cheek`, and `neck`. The target service accepts compressed `.target.gz` files directly. Run exact filenames from the directory inventory rather than assuming a slider name exists.

Add the rig **before** garments/body parts that should follow it; the asset loader uses that rig to transfer skinning. The default loader requests subdivision level 1; pass `subdiv_levels=0` deliberately where source strands or final polygon budget warrant it.

## License exceptions and alternatives

- `hair/o4saken_long01/o4saken_long01.mhclo` says **CC BY 4.0**, while the official pack page and JSON call it CC0. The style is also shorter/layered. It is not selected. If later needed, reconcile provenance or honor CC BY attribution rather than silently declaring it CC0.
- `skins/callharvey3d_midtoned_female/*.mhmat` contains an old AGPLv3 boilerplate despite the pack's CC0 record. Not selected; the verified system female skins avoid this ambiguity.
- [Blender Studio Human Base Meshes](https://www.blender.org/download/demo-files/) is another official CC0 anatomy source, version 1.4.1 requiring Blender 4.2+. It would be useful for sculpting comparison, but was not downloaded/tested here and does not establish a ready rigged skin/face pipeline equivalent to the acquired MPFB stack.
- [3D Scan Store free female head](https://www.3dscanstore.com/free-female-download) requires providing a name/email and joining a mailing list. Its [published license](https://www.3dscanstore.com/terms-and-conditions-licensing) restricts redistributing scan/model data and releasing derivatives under open-source licenses; free downloads cannot be used commercially without express permission. It was neither acquired nor selected for a freely redistributable browser asset.
- No superior scan source with both immediate no-signup acquisition and a verified permissive redistribution grant was established. This is a bounded source-selection conclusion, not a claim that none exists.

## Quality gate to preserve

A functioning anatomical mesh and valid license resolve acquisition and pipeline risk. They do not resolve portrait credibility. Evaluate actual renders for face proportions, brow density, eye/lid contact, tearline, hairline and skin pore scale. Inspect front, profile and three-quarter neutral views beside the references. Keep the initial source as an editable checkpoint, and do not label the result ultrarealistic solely because it is textured and rigged.
