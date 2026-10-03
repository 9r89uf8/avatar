"""Bake portable skin normal/roughness inputs, keeping source albedo independent."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'assets/textures';out.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4;s.cycles.use_denoising=False
body=bpy.data.objects['AvatarBody'];bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
mat=body.data.materials[0];ns=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
# Physically scaled tiny surface deviations, not gross sculpt displacement.
tex=next(n for n in ns if n.type=='TEX_NOISE');tex.inputs['Scale'].default_value=1200
coord=ns.new('ShaderNodeTexCoord');links.new(coord.outputs['Object'],tex.inputs['Vector'])
bump=next(n for n in ns if n.type=='BUMP');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.000065
rough=ns.new('ShaderNodeTexNoise');rough.inputs['Scale'].default_value=120;rough.inputs['Detail'].default_value=2;links.new(coord.outputs['Object'],rough.inputs['Vector'])
ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[0].color=(.38,.38,.38,1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(.57,.57,.57,1);links.new(rough.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],bs.inputs['Roughness'])
for kind,file in [('NORMAL','skin-normal.png'),('ROUGHNESS','skin-roughness.png')]:
 image=bpy.data.images.new(file,width=4096,height=4096,alpha=False);image.colorspace_settings.name='Non-Color';node=ns.new('ShaderNodeTexImage');node.image=image;ns.active=node
 s.render.bake.margin=16;s.render.bake.use_clear=True;s.render.bake.normal_space='TANGENT'
 bpy.ops.object.bake(type=kind,use_clear=True,margin=16)
 image.filepath_raw=str(out/file);image.file_format='PNG';image.save();print('BAKED',kind,image.filepath_raw,flush=True)
 ns.remove(node)
(ROOT/'reports/surface-bake.json').write_text(json.dumps({'resolution':4096,'normalConvention':'OpenGL tangent +Y','roughness':'linear scalar','source':'Project-authored physical-scale microrelief baked with Cycles','normalDistanceMeters':.000065,'notCapturedPores':True},indent=2))
