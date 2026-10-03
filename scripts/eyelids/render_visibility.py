import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];s=bpy.context.scene;o=bpy.data.objects['LidCandidate_Lashes'];print('LOC',o.matrix_world[:])
p=o.data.materials[0].node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1,0,0,1);p.inputs['Emission Color'].default_value=(1,0,0,1);p.inputs['Emission Strength'].default_value=1
s.cycles.samples=16;s.cycles.use_denoising=False;s.render.resolution_x=1800;s.render.resolution_y=2200;s.render.resolution_percentage=100;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=.29;s.render.border_max_x=.71;s.render.border_min_y=.60;s.render.border_max_y=.76;s.render.filepath=str(ROOT/'renders/eyelids/visibility-red-v2.png');bpy.ops.render.render(write_still=True)
