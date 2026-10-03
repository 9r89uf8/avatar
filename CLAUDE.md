# Avatar project instructions

Read docs/brief.md, docs/progress.md and the supplied Realistic Avatar Build Plan for Codex and Claude Code.md. Preserve uploaded references and the tracked rolldown dependency files. Use one writer for the Blender scene. Check asset licenses before including source or browser bytes.

Blender build: BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b --factory-startup --python-exit-code 1 -P scripts/blender/build_character.py
Review: BLENDER_USER_RESOURCES=$PWD/.runtime/blender blender -b scenes/avatar-master.blend --python-exit-code 1 -P scripts/blender/render_review.py -- --view portrait

Do not claim facial realism from a build, render success, or thumbnail. Inspect full-resolution source and browser screenshots. Keep true geometry and interoperable source files. No publishing, purchase or merge without explicit authorization.
