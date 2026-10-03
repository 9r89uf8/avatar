"""The isolated collar fix was accepted after source and actual-GLB comparisons.
Use export_avatar.py followed by verify_cloth_export.py; the old experiment is
intentionally disabled so it cannot apply the inverse-skin correction twice.
Evidence and old/new renders remain in reports/cloth-parity* and renders/.
"""
raise SystemExit('Use scripts/blender/export_avatar.py, then scripts/blender/verify_cloth_export.py. The correction is already integrated.')
