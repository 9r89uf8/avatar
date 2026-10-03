# Blender Avatar Agent Toolkit

Tool reference for a realistic full body adult female character using Codex or Claude Code. Sources reviewed on 1–2 October 2026; revised on 2 October 2026.

## Choose the delivery target first

Record the intended output and destination application before choosing the human source, hair representation or export route. Use this decision to select the relevant tools below; define the character's appearance in the later build brief.

| Intended output | Tool and asset implications |
| --- | --- |
| Still renders | Use Cycles, detailed skin maps and strand hair. Keep an editable `.blend`; prioritize the appearance at the final camera distance. |
| Rendered animation | Add a deforming rig, expressions and animation tests. Check hair and clothing throughout motion; retain Blender features when rendering in Blender. |
| Real-time avatar | Name the target engine or viewer and set geometry, texture and performance budgets. Prepare supported materials, hair cards or other compatible hair, a suitable skeleton and an early export test. |

For multiple outputs, retain a detailed Blender source and prepare a separate optimized delivery version. Confirm whether editable assets will be shared before purchasing character libraries.

## Recommended starting tools

Use Blender as the main application, version-controlled Python scripts for repeatable work, and one MCP connector for live inspection. Start from a suitable human mesh. The agent needs both image feedback and numeric checks to judge its work. This document defines tools and access methods; character-specific build instructions come later.

**Recommended baseline:** Blender 5.2.2 LTS, Blender Lab MCP, Blender command line, MPFB 2.0.17, system assets, Cycles, and the built-in material, hair and animation tools. This provides repeatable automation at no software-license cost. Choose Human Generator or scan assets when their starting quality better matches the target and their licenses permit the deliverable.

| Tool | Main job | Selection |
| --- | --- | --- |
| Blender and Python API `bpy` | Scene editing, geometry, materials, animation and export | Core |
| Blender command line | Repeatable scripts, validation and long renders | Core |
| Blender Lab MCP | Live scene inspection, Python execution, images and documentation | Default connector |
| MCP for Blender by ahujasid | Alternative connector with asset and generation integrations | Optional alternative |
| MPFB 2 | Free parametric human base, assets and rig options | Default human source |
| Human Generator | Prepared humans with a documented Python API | Paid alternative |
| Cycles and shader nodes | Lighting, skin, eyes and final renders | Core |
| Hair Curves and Geometry Nodes | Strand hair, brows, lashes and grooming | As needed |
| Armatures, Rigify and Shape Keys | Posing, expressions and deformation | For a poseable avatar |
| Sculpting, Multiresolution and UV tools | Shape refinement and texture preparation | As needed |
| Substance 3D Painter | Detailed texture authoring | Optional paid tool |
| Marvelous Designer | Custom garments and cloth simulation | Optional paid tool |

Character Creator, Daz Studio, MetaHuman and Blender Studio base meshes are other human-source routes. Poly Haven, MPFB packs and scan suppliers provide assets. Meshy and other generators can supply drafts or accessories. Choose additions for a concrete requirement rather than installing every option.

**Version policy:** record the exact Blender build, connector release or commit, extension versions and asset packs once a small end-to-end test succeeds. A minimum Blender requirement is not proof of compatibility for the whole project. Repository examples on `main` or `master` can differ from an installed release.

Sources: [Blender download](https://www.blender.org/download/), [Blender Lab MCP](https://www.blender.org/lab/mcp-server/), [MPFB release](https://static.makehumancommunity.org/mpfb/releases/release_2017.html).

## Agent control and local execution

### Blender Python API

`bpy` edits Blender data and runs Blender operations. Use `bpy.data` for direct data access, `bpy.ops` for operators, and `bmesh` for mesh operations where appropriate. Operators can depend on mode, selection and editor context. Prefer explicit names and parameters, and inspect the installed API before relying on old examples.

Run scripts in Blender's embedded Python through a live connector, the Python console, or the command line. The external MCP server has its own Python environment. Installing a package there does not install it inside Blender.

```python
import bpy
print(bpy.app.version_string)
print([(obj.name, obj.type) for obj in bpy.data.objects])
```

### Blender command line

Use background Blender processes for reproducible jobs and long renders. With `blender` on PATH and an existing scene, the following executes a project-owned script and reports Python failure through the process exit code:

```bash
blender --background avatar.blend --python-exit-code 1 --python scripts/inspect.py
```

Argument order matters. A background process opens its own copy of the saved scene; it does not change another window's unsaved scene. Save the intended input first and give output files explicit paths. In PowerShell, prefix a quoted executable path with `&`. Some UI-dependent add-ons need an interactive Blender session.

Sources: [Python API](https://docs.blender.org/api/current/), [Command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html).

### Codex and Claude Code

| Capability | Codex | Claude Code |
| --- | --- | --- |
| Register local server | `codex mcp add NAME -- COMMAND` | `claude mcp add --transport stdio NAME -- COMMAND` |
| Inspect connections | `codex mcp list` or `/mcp` | `claude mcp list` or `/mcp` |
| Project instructions later | `AGENTS.md` | `CLAUDE.md` |
| Visual feedback | Use the session's image-viewing capability | Use image reading or returned MCP images |

Use a vision-capable session. An image path is useful only if the agent can actually open the image. Tool names and image handling vary by client. Initially run the agent, connector and Blender on the same workstation; a hosted agent cannot automatically reach Blender on a laptop.

Sources: [Codex MCP](https://developers.openai.com/codex/mcp), [Claude Code MCP](https://code.claude.com/docs/en/mcp).

### Supporting utilities and optional standalone bpy

The terminal, file editor and Git support scripts, logs and settings. Keep `.blend` checkpoints and large assets in appropriate file storage. `uv` and `uvx` launch isolated Python tools such as the community connector.

The official standalone `bpy` package is an optional automation route, not a prerequisite for installed Blender. PyPI currently lists `bpy==5.2.2` with Python `3.13.*`. Use it only for a pipeline that needs Blender as a Python package; verify available wheels, add-ons and rendering support for that environment.

Sources: [uv tools](https://docs.astral.sh/uv/concepts/tools/), [bpy package](https://pypi.org/project/bpy/).

## Connecting through MCP

MCP means Model Context Protocol. It standardizes tool calls between an AI client and external software. It is useful for live Blender control, but is optional when the agent can execute Blender scripts directly. Blender Lab MCP and the community MCP for Blender are separate projects; their tool names and configuration differ.

### Blender Lab MCP

This is Blender's own Lab project, delivered as an add-on plus a separate MCP process. It requires Blender 5.1+ and an external Python environment at 3.10+. The latest repository release checked was `v1.0.3`, dated 11 September 2026. Blender presents Lab MCP as an experiment; pin the release and pass the installation checks before starting character work.

Install the add-on using the [Blender Lab project page](https://www.blender.org/lab/mcp-server/) or its extension repository. Install the server into a dedicated Python environment using the source route documented by the project:

```bash
python -m pip install "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp"
```

With that environment activated and its `blender-mcp` executable on PATH, register the client you use:

```bash
codex mcp add blender-lab -- blender-mcp
claude mcp add --transport stdio blender-lab -- blender-mcp
```

For reliable launches, configure the absolute path to that environment's executable. On Windows it is under `Scripts`; on macOS/Linux it is under `bin`. Use the matching add-on release. In Blender, enable **Edit → Preferences → System → Network → Allow Online Access**, then start the add-on's server. The official add-on checks `bpy.app.online_access` and refuses to start when it is false, even for a localhost connection. Restart the client and inspect its actual tool list. The command above pins the checked release; upgrade deliberately after testing.

Sources: [Official server installation](https://projects.blender.org/lab/blender_mcp/src/branch/main/mcp/README.md), [Releases](https://projects.blender.org/lab/blender_mcp/releases), [Server metadata](https://projects.blender.org/lab/blender_mcp/src/branch/main/mcp/pyproject.toml), [Add-on startup checks at v1.0.3](https://projects.blender.org/lab/blender_mcp/src/tag/v1.0.3/addon/blender_mcp_addon/__init__.py).

### Community MCP for Blender

The ahujasid project is now named `mcp-for-blender`; its published version checked was `2.1.3`, released 30 September 2026. It adds asset and generation integrations. Use it as an alternative when those integrations are useful.

```bash
uvx mcp-for-blender@2.1.3 install-addon
codex mcp add blender-community -- uvx mcp-for-blender@2.1.3
claude mcp add --transport stdio blender-community -- uvx mcp-for-blender@2.1.3
```

Enable the installed add-on and start its server. Use one controlling client and connector per scene initially. Both connectors default to port 9876. Installing `blender-mcp` from PyPI selects the legacy community package name, not Blender Lab's repository implementation. Use separate environments and explicit executable paths to avoid that collision.

Sources: [Community setup](https://github.com/ahujasid/mcp-for-blender), [Published package](https://pypi.org/project/mcp-for-blender/).

### Execution security and telemetry

Blender warns that its Lab connector executes generated code without guards against deleting files or sending data away. Follow its recommendation to use a virtual machine or a machine without access to sensitive information. Isolate Blender itself, because Blender executes the code; a virtual environment for the MCP Python process only separates package dependencies. Keep scene checkpoints and keep the Blender connection on localhost.

For the community connector, set `BLENDER_MCP_SAFE_MODE=1` in the **MCP server's environment**. It is off by default. The code filter blocks categories such as direct file access, subprocesses and networking while allowing ordinary Blender operations. Treat this as an extra check; Blender still has its operating-system permissions. Test third-party add-on calls in a disposable scene because the filter may reject custom scripts.

The `2.1.3` package documentation distinguishes two telemetry levels: basic usage metrics are collected by default; prompts, generated code, screenshots, scene data and trajectory content require opt-in. The project says collected telemetry may be used for research and AI training. Set `DISABLE_TELEMETRY=true` in the MCP server's environment to disable all telemetry, and leave the add-on's content-consent option unchecked. Existing installations may retain earlier consent settings, so check the actual preference.

Recommended community server environment entries:

```json
{
  "BLENDER_MCP_SAFE_MODE": "1",
  "DISABLE_TELEMETRY": "true"
}
```

These are environment entries, not a complete client configuration. Put them in the server's `env` configuration or pass them through the client's environment options.

Sources: [Blender security warning](https://www.blender.org/lab/mcp-server/), [Community safe mode and telemetry at 2.1.3](https://pypi.org/project/mcp-for-blender/2.1.3/), [Community terms](https://github.com/ahujasid/mcp-for-blender/blob/main/TERMS_AND_CONDITIONS.md).

### Timeout boundaries

Codex's MCP tool timeout defaults to 60 seconds. Increasing it does not remove server-side limits: the checked Lab source has a 300-second live socket timeout and a 120-second CLI helper timeout. Submit long renders through the agent's own shell as managed jobs.

Sources: [Lab live connection](https://projects.blender.org/lab/blender_mcp/src/branch/main/mcp/blmcp/tools_helpers/connection.py), [Lab CLI helper](https://projects.blender.org/lab/blender_mcp/src/branch/main/mcp/blmcp/tools_helpers/blender_cli.py), [Codex MCP configuration](https://developers.openai.com/codex/mcp).

## MCP tools and visual feedback

Discover the installed server's tool schemas before calling them. The following 26 names were checked against the official `v1.0.3` tool catalog. They were not exercised in a local Blender session for this document.

### Blender Lab tool catalog

| Tool or tool family | What it does and when to use it |
| --- | --- |
| `execute_blender_code` | Runs Python in the live scene. Return structured data in a JSON-serializable dictionary named `result`. |
| `execute_blender_code_for_cli` | Runs Python in a background Blender process. Use for bounded checks of saved scenes. |
| `get_objects_summary` and `get_object_detail_summary` | Inspect scene hierarchy and a named object. |
| `get_blendfile_summary_datablocks` | Report scene data counts and current state. |
| `get_blendfile_summary_datablocks_for_cli` | Open a saved `.blend` in background Blender and report its data counts. |
| `get_blendfile_summary_missing_files` | Find missing external dependencies such as textures. |
| `get_blendfile_summary_missing_files_for_cli` | Check a saved `.blend` for missing dependencies in background Blender. |
| `get_blendfile_summary_of_linked_libraries` and `get_blendfile_summary_path_info` | Inspect linked files and save/path information. |
| `get_blendfile_summary_of_linked_libraries_for_cli` and `get_blendfile_summary_path_info_for_cli` | Inspect a saved `.blend` for linked libraries and path/save information. |
| `get_blendfile_summary_usage_guess` and `get_blendfile_summary_usage_guess_for_cli` | Heuristically classify a live or saved scene's likely uses; treat the scores as guesses. |
| `get_screenshot_of_area_as_image` and `get_screenshot_of_window_as_image` | Return images of the viewport or window. |
| `get_screenshot_of_window_as_json` | Describe interface layout and selection in structured form. |
| `render_thumbnail_to_path` and `render_viewport_to_path` | Write a small preview or a render using scene settings. |
| `jump_to_view3d_object_by_name` and `jump_to_tab_by_name` | Frame an object or change the workspace. |
| `jump_to_view3d_object_data_by_name` | Frame the object that owns the named data block. |
| `jump_to_tab_by_space_type` | Switch to a workspace whose main area has the requested editor type. |
| `search_api_docs`, `get_python_api_docs`, `search_manual_docs` | Read bundled API and manual documentation. Check its version against Blender. |

Sources: [Official tool list at v1.0.3](https://projects.blender.org/lab/blender_mcp/src/tag/v1.0.3/readme_tools.rst), [Python result contract](https://projects.blender.org/lab/blender_mcp/src/branch/main/mcp/blmcp/tools/execute_blender_code.py).

### Render output paths

In Lab `v1.0.3`, both `render_thumbnail_to_path` and `render_viewport_to_path` discard the directory in the supplied `output_path`. They keep its basename and write under `os.path.join(bpy.app.tempdir, "blender_mcp", basename)`. Read the returned `filepath`, open that actual file for review, and copy images that must be retained into the project's `renders/` folder. Use unique filenames to avoid collisions. For direct project-folder output or long renders, use a project-owned Blender Python/CLI job with an explicit `scene.render.filepath`.

Sources: [Thumbnail implementation at v1.0.3](https://projects.blender.org/lab/blender_mcp/src/tag/v1.0.3/mcp/blmcp/tools/render_thumbnail_to_path_toolcode.py), [Viewport render implementation at v1.0.3](https://projects.blender.org/lab/blender_mcp/src/tag/v1.0.3/mcp/blmcp/tools/render_viewport_to_path_toolcode.py).

### Community tool catalog

The corresponding community tools include `get_scene_info`, `get_object_info`, `get_viewport_screenshot`, `execute_blender_code`, `bpy_api_lookup`, `describe_node_type` and `export_scene`. Optional Poly Haven tools search, preview and download assets. Other integrations have their own credentials, licenses and service costs. Do not interchange the two servers' names or return conventions.

Source: [Community tool implementation](https://github.com/ahujasid/mcp-for-blender/blob/main/src/blender_mcp/server.py).

### Choose the right feedback

Use viewport screenshots for placement, silhouette, intersections and pose. Use small thumbnails for framing, broad lighting and large material errors. Use camera renders and close-ups for skin, eyes, hands and hairlines. Combine images with Python inspection of dimensions, topology, weights, missing files and material assignments.

Lab `v1.0.3` sets the thumbnail's long side to 320 pixels and reduces Cycles to 16 samples. Its EEVEE sample override checks the older `BLENDER_EEVEE_NEXT` identifier, so verify EEVEE settings against the installed Blender version. Use larger camera renders to judge pores, eyelashes and other fine details. Render time depends on scene complexity and hardware.

Sources: [Thumbnail implementation at v1.0.3](https://projects.blender.org/lab/blender_mcp/src/tag/v1.0.3/mcp/blmcp/tools/render_thumbnail_to_path_toolcode.py), [Blender 5.0 engine identifier change](https://developer.blender.org/docs/release_notes/5.0/python_api/).

## MPFB scripting reference

MPFB is the free default for an inspectable Blender workflow. Install the extension and the separate `makehuman_system_assets` pack. MakeHuman desktop is not required. MPFB 2.0.17 requires Blender 4.2 or newer. Add and configure the rig before loading body parts and clothing that should follow it.

MPFB supports Python automation for creation, morphs, skins, assets, rigs and export. Use its service documentation and scripting samples, and match service signatures to the installed release.

Sources: [Getting started](https://static.makehumancommunity.org/mpfb/docs/getting_started.html), [Scripting samples](https://github.com/makehumancommunity/mpfb2/blob/master/script_samples/index.md).

### Import and parameter rules

Blender Extensions add a variable prefix to module paths. The upstream samples include a `dynamic_import` helper that locates loaded MPFB modules. Use the helper appropriate to the installed version; do not assume a fixed import prefix. MPFB must already be enabled.

**Required female-base setting:** MPFB defines `gender=0.0` as the female endpoint and `1.0` as the male endpoint. Its default macro dictionary uses `0.5`, the neutral midpoint. For this character, explicitly set `0.0` when creating the base, or verify that the selected preset already supplies it. Reapply macro details after changing the property on an existing human.

The following illustrates the parameter update after resolving `HumanService`, `HumanObjectProperties` and `TargetService` using the upstream import helper. It is an API illustration, not a complete character script:

```python
human = HumanService.create_human()
HumanObjectProperties.set_value("gender", 0.0, entity_reference=human)
TargetService.reapply_macro_details(human)
```

Sources: [Model parameter documentation](https://github.com/makehumancommunity/mpfb2/blob/master/docs/ui/model/model.md), [MHM gender mapping](https://github.com/makehumancommunity/mpfb2/blob/master/docs/fileformats/mhm.md), [Default macro dictionary](https://github.com/makehumancommunity/mpfb2/blob/master/src/mpfb/services/targetservice.py), [Basic-human sample](https://github.com/makehumancommunity/mpfb2/blob/master/script_samples/01_create_a_basic_human.py).

### Useful service interfaces

| Interface | Use and prerequisites |
| --- | --- |
| `HumanService.create_human` | Create a human mesh; accepts macro settings. |
| `HumanObjectProperties.set_value` and `TargetService.reapply_macro_details` | Set macro proportions and reapply their geometry effects. |
| `TargetService.load_target` | Apply a specific detail morph. Discover real target identifiers first. |
| `HumanService.set_character_skin` | Apply a resolved `.mhmat` skin; `ENHANCED_SSS` is one supported mode. |
| `AssetService.find_asset_absolute_path` | Resolve installed assets and detect missing content. |
| `HumanService.add_mhclo_asset` | Load body parts or clothes with the correct asset type and options. |
| `HumanService.add_builtin_rig` | Add a built-in rig; `rigify.human` selects a Rigify meta-rig. |
| `RigService.generate_rigify_rig` | Generate controls after checking Rigify is enabled; retain the meta-rig for regeneration. |

Sources: [Skin example](https://github.com/makehumancommunity/mpfb2/blob/master/script_samples/05_setting_skin.py), [Asset example](https://github.com/makehumancommunity/mpfb2/blob/master/script_samples/06_adding_basic_assets.py), [Rigify example](https://github.com/makehumancommunity/mpfb2/blob/master/script_samples/04_adding_and_generating_rigify.py).

Keep the selected preset, morph values and asset paths in project configuration. Separate body-generation success from visual quality. MPFB core/system assets offer a useful starting point, but close-up skin, eyes, hair and deformation still require evaluation. Check every asset pack's license: the official list includes both CC0 and attribution-required packs.

Source: [Asset pack catalog and licenses](https://static.makehumancommunity.org/assets/assetpacks.html).

## Other human sources and quality upgrades

### Human Generator

Paid Blender-native alternative with prepared characters and a documented `Human` Python API. V4 is a software version; Human Generator Ultimate is the current product listing. The vendor's seller listing includes Blender 3.6 through 5.2. Test the purchased build and content packs before making them a project dependency.

```python
import bpy
from HumGen3D import Human
presets = Human.get_preset_options("female")
human = Human.from_preset(presets[0], context=bpy.context)
```

The preset index is illustrative; choose the intended asset explicitly. HumGen's current homepage and custom-hair documentation describe particle hairstyles; preserve that representation unless an explicit conversion is needed. Its license restricts sharing models and textures with recipients who lack a license, even after customization. Check that before choosing it for a downloadable avatar rather than rendered images.

Sources: [Human API](https://help.humgen3d.com/API/Overview), [Seller compatibility](https://superhivemarket.com/products/humgen3d), [Current product features](https://humgen3d.com/), [Hair documentation](https://help.humgen3d.com/customhair), [License FAQ](https://help.humgen3d.com/license).

### Character Creator and Blender Auto Setup

Commercial character ecosystem with a free Blender bridge. Use Blender-side Python and the CC/iClone Python pipeline plugin for transfer and round trips. Verify the specific creation and morph operations needed by the project. Auto Setup's current download page lists 2.4.0, Blender 4.2 LTS+, Windows, and CC 5.07+/4.67+.

Sources: [Auto Setup requirements](https://www.reallusion.com/auto-setup/blender/download.html), [CC Python pipeline plugin](https://github.com/soupday/CCiC-Blender-Pipeline-Plugin).

### Daz Studio and Diffeomorphic

Useful when the desired character or wardrobe already exists in the Genesis ecosystem. Daz uses its own ECMAScript-derived scripting language; Diffeomorphic supplies Blender import and scripting capabilities. Follow the importer's matching scene/data export procedure and verify shading and deformation after import. The maintainer wiki currently lists stable 5.2.0. Asset purchases and redistribution terms depend on the selected content.

Sources: [Daz scripting](https://docs.daz3d.com/public/software/dazstudio/4/referenceguide/scripting/start), [Diffeomorphic](https://github.com/Diffeomorphic/import_daz/wiki).

### MetaHuman

A legitimate automation option when an Unreal-based character pipeline is acceptable. Epic now documents Python creation, editing, conforming, assembly and export in Unreal Engine 5.8 or later. Texture and auto-rig requests involve Epic's cloud services and sign-in.

For a Blender destination, validate the transfer before committing to this route. The documented DCC package includes DNA, texture and metadata files; it is not simply a complete Blender-ready character in an FBX. Materials, hair and rig behavior need an explicitly tested conversion path. Review current Epic terms for the intended use.

Sources: [MetaHuman Python API](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-python-scripting-in-unreal-engine?lang=en-US), [Export tools](https://dev.epicgames.com/documentation/metahuman/metahuman-creator-export-tool-in-unreal-engine?lang=en-US).

### Blender Studio base meshes and scanned humans

The free CC0 Human Base Meshes bundle is useful for custom sculpting and topology work, but does not supply a finished shaded and animated character. Paid 3D Scan Store assets and Texturing.xyz maps can improve anatomical or skin detail. Inspect package contents, topology, UVs and license; a face map is not a full-body solution and a scan is not automatically rigged. The agent imports, aligns and transfers data as needed.

Sources: [Blender demo assets](https://www.blender.org/download/demo-files/), [Body scans](https://www.3dscanstore.com/retopologised-body-models/animation-ready-body-scans), [VFace displacement](https://texturing.xyz/pages/vface-multi-channel-displacement).

## Blender tools for the finished character

### Python identifiers for Blender 5.2

The following identifiers were reviewed against Blender 5.2 documentation. Inspect the installed 5.2.2 build's API during setup. In this table, `scene` is a Blender scene, `obj` is the intended object, and `nodes` is a material's shader-node collection; names such as `bsdf` and `hair` refer to nodes created by the agent.

| Task | Exact identifier or API |
| --- | --- |
| Cycles renderer | `scene.render.engine = "CYCLES"` |
| EEVEE renderer in Blender 5.x | `scene.render.engine = "BLENDER_EEVEE"`; Blender 5.0 renamed the older `BLENDER_EEVEE_NEXT` identifier. |
| Principled surface shader | `nodes.new("ShaderNodeBsdfPrincipled")` |
| Cycles skin scattering method | `bsdf.subsurface_method = "RANDOM_WALK_SKIN"`; also configure a nonzero subsurface contribution and appropriate skin maps. |
| Principled hair shader | `nodes.new("ShaderNodeBsdfHairPrincipled")`; `hair.model = "HUANG"`; `hair.parametrization = "MELANIN"` when using melanin controls. |
| Geometry and deformation modifiers | `obj.modifiers.new(name, type=...)` with `"SUBSURF"`, `"MULTIRES"`, `"NODES"`, `"ARMATURE"`, `"CLOTH"`, `"COLLISION"` or `"DISPLACE"` as appropriate. |
| Mesh editing in Object Mode | `bmesh.new()`, `bm.from_mesh(mesh)`, `bm.to_mesh(mesh)`, `bm.free()` for a Python-owned BMesh. |
| Mesh editing in Edit Mode | `bmesh.from_edit_mesh(mesh)` and `bmesh.update_edit_mesh(mesh)` for the Blender-owned edit mesh. |
| Existing expression or corrective shape key | `obj.data.shape_keys.key_blocks[name].value`; first check that the shape key exists. |
| Rigify generation | `bpy.ops.pose.rigify_generate()` with Rigify enabled and a valid active meta-rig/context; use MPFB's rig service for MPFB's asset parenting. |
| glTF or FBX export | `bpy.ops.export_scene.gltf(...)` or `bpy.ops.export_scene.fbx(...)`; inspect the installed parameters and apply the destination's export settings. |

`subsurface_method`, `model` and `parametrization` are node properties. Shader socket names and availability are separate and can change with node mode or version. Inspect them before wiring a material:

```python
print(bpy.app.version_string)
print([(socket.name, socket.identifier) for socket in bsdf.inputs])
print([
    item.identifier
    for item in bsdf.bl_rna.properties["subsurface_method"].enum_items
])
```

Sources: [Blender 5.0 EEVEE rename](https://developer.blender.org/docs/release_notes/5.0/python_api/), [Blender 5.2 renderer API](https://docs.blender.org/api/5.2/bpy.types.RenderSettings.html), [Principled shader API](https://docs.staging.blender.org/api/current/bpy.types.ShaderNodeBsdfPrincipled.html), [Principled Hair API](https://docs.staging.blender.org/api/current/bpy.types.ShaderNodeBsdfHairPrincipled.html), [Modifier identifiers](https://docs.blender.org/api/5.2/bpy_types_enum_items/object_modifier_type_items.html), [BMesh API](https://docs.blender.org/api/5.2/bmesh.html), [Shape-key API](https://docs.blender.org/api/5.2/bpy.types.ShapeKey.html), [Rigify operator](https://github.com/blender/blender-addons/blob/main/rigify/ui.py), [Export API](https://docs.blender.org/api/5.2/bpy.ops.export_scene.html). The two official staging shader pages identified themselves as 5.2 when checked; their `current` URLs can advance.

### Skin eyes and rendering

Use Principled BSDF and shader nodes for skin, eyes, nails and clothing. The agent connects color, roughness, normal and displacement data with the correct mapping and color interpretation. Subsurface scattering helps describe skin, but geometry, scale, texture quality and lighting jointly determine the result.

Use Cycles for final renders in the default workflow. Use EEVEE for fast previews or an EEVEE delivery target; it supports subsurface effects. Check material support in the selected engine and compare final-camera renders.

Sources: [Principled BSDF](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html), [Cycles](https://docs.blender.org/manual/en/latest/render/cycles/index.html), [EEVEE materials](https://docs.blender.org/manual/en/latest/render/eevee/material_settings.html).

### Hair Curves Geometry Nodes and hair shaders

Use curves and procedural grooming for scalp hair, brows, lashes and fine hair. The agent imports or creates guides, binds them to the intended surface, and adjusts density, clumping and variation. Existing grooms can be a better starting point than an entirely scripted hairstyle.

Principled Hair BSDF is a Cycles-only shader. Its Huang model is worth evaluating for detailed close-ups; Blender's release documentation specifically highlights its close-up improvements. Inspect the current shader inputs instead of hard-coding old socket indices. A real-time destination may need cards or other exported geometry instead of rendered strands.

Sources: [Hair nodes](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/hair/index.html), [Principled Hair](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/hair_principled.html), [Huang improvements](https://www.blender.org/download/releases/4-2/).

### Armatures Rigify and Shape Keys

Preserve a suitable supplied rig, or use Rigify to generate controls from a fitted meta-rig. Shape keys store expressions, lip movements and corrective deformations. The agent can set poses and weights through Python. Test shoulders, hips, elbows, knees and fingers; generating a rig is not proof of good skinning. Preserve topology when existing shape keys depend on vertex correspondence.

Sources: [Rigify](https://docs.blender.org/manual/en/latest/addons/rigify/index.html), [Shape keys](https://docs.blender.org/manual/en/latest/animation/shape_keys/introduction.html).

### Sculpting subdivision and surface detail

Use mesh editing, subdivision and Multiresolution to refine silhouette, anatomy and detail. Fine artistic sculpting is less predictable to automate than numeric adjustments. Retain a sound base and compare multiple views. Topology-changing operations can invalidate existing UVs, weights or shape keys; transfer those deliberately when needed.

### Clothing cloth and lighting

Blender mesh tools and Cloth/Collision modifiers can produce and drape clothing. An agent can create procedural garments; libraries or Marvelous Designer may provide better starting results for complex tailoring. Area lights, HDRIs and fixed cameras make comparisons consistent. Keep camera, exposure and lighting stable when judging a material change.

### UV maps baking and export

Use UV tools and baking to prepare textures and exportable detail. Keep an editable `.blend` as the working source. Export GLB for suitable viewers or FBX for compatible animation pipelines, with destination-specific settings. Reopen the export in its target application: Blender hair, node materials and rig controls do not all transfer unchanged.

Sources: [Blender manual](https://docs.blender.org/manual/en/latest/), [Import and export](https://docs.blender.org/manual/en/latest/files/import_export.html).

## Specialist tools and asset services

### Substance 3D Painter

Paid texture authoring for skin variation, makeup, clothing and local details. Use it when supplied textures need substantial authoring. The `substance_painter` Python API covers projects, baking, layers and texture export. Adobe also documents local HTTP execution of Python or JavaScript after launching the app with `--enable-remote-scripting`. The application must be running and ready; MCP is not required.

Sources: [Painter API](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/api/api-overview), [Remote scripting](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/tutorials/remote-control).

### Marvelous Designer

Paid garment pattern design and cloth simulation. The official Python APIs cover import/export, patterns, fabrics and simulation utilities. Run scripts through the application or registered Python plug-ins, then transfer garments to Blender. Use the documented application scripting route; establish headless support separately if the deployment needs it.

Sources: [Marvelous API](https://developer.marvelousdesigner.com/), [Simulation examples](https://developer.marvelousdesigner.com/scenario.html).

### Asset libraries

| Source | What to use it for | Agent access |
| --- | --- | --- |
| MPFB packs | Skins, body parts, hair, clothes and poses | Install packs; resolve files through AssetService |
| Poly Haven | HDRI lighting and PBR scene materials | Download files or use community MCP tools |
| Sketchfab and other marketplaces | Selected props, shoes and accessories | Approved downloads or a supported connector |
| Scan suppliers | Scanned geometry and skin detail | Import licensed local files; transfer maps as needed |

Keep an asset manifest with source, selected package, license, file paths, texture channels and UV assumptions. Poly Haven assets are CC0; other libraries and even different MPFB packs can carry different terms. A downloaded material's UV layout and scale must fit the selected mesh.

Sources: [MPFB pack licenses](https://static.makehumancommunity.org/assets/assetpacks.html), [Poly Haven license](https://polyhaven.com/license), [Community asset integrations](https://github.com/ahujasid/mcp-for-blender).

### Meshy and other generative services

Meshy exposes REST APIs and an official `@meshy-ai/meshy-mcp-server` for clients including Codex and Claude Code. Configure its API credentials using the current guide, submit a job, poll status and import the downloaded result. Usage consumes service credits. The community Blender connector also integrates other generation providers; requirements vary.

Use generation for experiments, rough assets or accessories. Promote a generated human to the main character source only after inspecting its anatomy, separate parts, UVs, topology, material channels and deformation in Blender.

Sources: [Meshy MCP](https://docs.meshy.ai/en/api/ai), [Meshy rigging requirements](https://docs.meshy.ai/en/api/rigging).

## Budget snapshot

Prices below were checked on 2 October 2026 and are in US dollars unless stated as credits. They cover selected software and services; budget separately for the coding-agent plan or API usage, hardware, rendering and additional assets. Regional pricing, taxes, promotions and purchase terms can change the final amount.

| Tool or purchase | Checked price | What the amount covers |
| --- | --- | --- |
| Blender, Lab MCP, community MCP core, MPFB and Blender's built-in tools | $0 software license cost | The default local tool stack; optional generation services and purchased content cost extra. |
| Human Generator Ultimate Personal/Portfolio | $68 | Product purchase for personal, portfolio and educational use. |
| Human Generator Ultimate Commercial | $128 | Product purchase for commercial use; both listed tiers include all features and content. Asset-sharing restrictions still apply. |
| Adobe Substance 3D Collection for individuals | $59.99/month | Current listed subscription including Painter and the other Collection apps. Review the selected billing terms at checkout. |
| Marvelous Designer Personal monthly | $39/month | Automatically renewing monthly subscription, cancelable anytime. |
| Marvelous Designer Personal one-year prepaid | $280 | One payment for one year; does not automatically renew. |
| Meshy API example using `meshy-7.1` | 20 credits mesh-only; 30 with 2K/4K textures; 35 with 8K textures | One image-to-3D request at standard geometry settings; auto-rigging adds 5 credits per request. Purchase API credits separately. |

Check Adobe's current purchase options for lower-cost Texturing-only plans before selecting the full Collection. Choose Character Creator editions, Daz content, scans and other paid packs individually after the delivery target is fixed; their package and usage rights determine the cost.

Sources: [Blender download](https://www.blender.org/download/), [MPFB extension](https://extensions.blender.org/add-ons/mpfb/), [Human Generator seller pricing](https://superhivemarket.com/products/humgen3d), [Adobe current plans](https://www.adobe.com/products/substance3d/plans.html), [Adobe pricing FAQ](https://helpx.adobe.com/substance-3d/pricing-change.html), [Marvelous license prices](https://support.marvelousdesigner.com/hc/en-us/articles/47358269350041-What-kind-of-licenses-does-Marvelous-Designer-offer), [Meshy API pricing](https://docs.meshy.ai/en/api/pricing).

## Validation and project setup

### Recommended project organization

Keep tool setup and character design separate so either Codex or Claude Code can use the same assets and scripts.

| Project item | Contents |
| --- | --- |
| `docs/toolkit.md` | This tool reference, with versions updated after setup |
| `AGENTS.md` or `CLAUDE.md` | Short entry point linking to the reference and later build instructions |
| `scripts/` | Reusable creation, inspection, rendering and export scripts |
| `config/` | Character settings, asset manifest and version record |
| `references/` | Approved visual references |
| `scenes/`, `renders/`, `exports/` | Scene checkpoints, review images and delivery files |

Keep repeatable changes in scripts or saved configuration even when discovered interactively through MCP. Serialize scene mutations: other agents can review images or research independently, but should not edit the same live scene at once.

### Installation acceptance checks

These checks establish that the tools are connected, not that the avatar is finished.

1. Verify the Blender version, executable path and selected renderer on the actual machine.
2. Install one connector and confirm its tool list. For Lab MCP, verify Allow Online Access; for the community connector, verify safe mode and telemetry settings. Read scene information and obtain an image the agent can open using the actual returned path.
3. Enable the chosen human generator and its required content. Confirm basic mesh creation and asset resolution in a disposable scene.
4. Save a checkpoint, reopen it in a separate Blender job and produce a camera render. Confirm textures are available.
5. If another application is the destination, export a small test character and verify its scale, materials and deformation there before a large build.

## Visual review and build brief

### Reference images and image tools

Supply consistent front, side and three-quarter references plus face, hair and clothing details where available. The agent's image viewer is essential for comparisons. Image-generation tools can help establish a concept, but generated references may disagree across views; resolve those contradictions in the character brief before treating them as geometry requirements.

### Evidence required during later character work

| Check | Evidence |
| --- | --- |
| Whole-body shape | Fixed front, side and three-quarter camera renders |
| Skin eyes and hair | Face and hairline close-ups at adequate resolution |
| Hands feet and clothing | Detail images plus intersection checks |
| Poseability | Test poses and deformation review |
| Technical integrity | Dimensions, mesh and material inspection, missing-file report |
| Reproducibility | Saved parameters, scripts, asset manifest and scene checkpoint |
| Delivery | Export reopened and checked in the intended application |

A successful script or a thumbnail is not a substitute for these checks. Start with inexpensive previews and raise quality where detail needs examination; do not spend full-render time on every small parameter change.

### Decisions for the later build brief

With the delivery target recorded at the start, define adult age and appearance, proportions, skin tone, hair, clothing, reference images, pose, expression needs, machine and GPU, budget, and file formats. Use these requirements to finalize the human source, detail level and optional tools.

**Verification scope:** this toolkit combines documentation and source-code review. No Blender installation, connector connection, character generation or visual-quality benchmark was executed for this document. Examples must pass the installation acceptance checks on the selected machine and versions.
