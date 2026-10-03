"""Isolated physically-scaled Cycles skin comparison; no source overwrite."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
m=bpy.data.materials['Skin'];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.subsurface_method='RANDOM_WALK_SKIN';p.inputs['Subsurface Weight'].default_value=1;p.inputs['Subsurface Scale'].default_value=.0012;p.inputs['Subsurface Radius'].default_value=(1,.45,.22);p.inputs['Subsurface Anisotropy'].default_value=.8
s=bpy.context.scene;s.cycles.samples=128;s.cycles.use_denoising=False;s.render.filepath=str(ROOT/'renders/skin-scattering-variant.png')
bpy.ops.render.render(write_still=True)
