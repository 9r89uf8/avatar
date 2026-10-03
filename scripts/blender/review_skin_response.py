"""Isolated anatomical roughness study, authored rather than measured skin."""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=args[0] if args else 'new'
s=bpy.context.scene;b=bpy.data.objects['AvatarBody'];m=bpy.data.materials['Skin'];ns=m.node_tree.nodes;lk=m.node_tree.links;p=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
if mode=='new':
 sample=b.shape_key_add(name='_roughness_position_sample',from_mix=True);positions=[v.co.copy() for v in sample.data];b.shape_key_remove(sample)
 attr=b.data.color_attributes.new(name='AuthoredRoughnessZones',type='FLOAT_COLOR',domain='POINT')
 for i,(x,y,z) in enumerate(positions):
  front=max(0,min(1,(-y-.07)/.028));rough=.52
  forehead=math.exp(-(x/.052)**4-((z-1.539)/.023)**4)
  nose=math.exp(-(x/.013)**4-((z-1.463)/.031)**4)
  lips=math.exp(-(x/.025)**4-((z-1.419)/.0057)**4)
  rough-=front*(.080*forehead+.175*nose+.145*lips)
  rough+=.006*math.sin(x*891+z*234)*math.sin(z*673-y*182)
  rough=max(.3,min(.56,rough));attr.data[i].color=(rough,rough,rough,1)
 co=ns.new('ShaderNodeVertexColor');co.layer_name=attr.name
 emit=ns.new('ShaderNodeEmission');lk.new(co.outputs['Color'],emit.inputs['Color']);output=next(n for n in ns if n.type=='OUTPUT_MATERIAL');lk.new(emit.outputs[0],output.inputs['Surface'])
 im=bpy.data.images.new('skin-zonal-roughness.png',width=2048,height=2048,alpha=False);im.colorspace_settings.name='Non-Color';t=ns.new('ShaderNodeTexImage');t.image=im;ns.active=t
 bpy.ops.object.select_all(action='DESELECT');b.select_set(True);bpy.context.view_layer.objects.active=b;s.cycles.samples=1;s.render.bake.margin=12;bpy.ops.object.bake(type='EMIT',margin=12)
 im.filepath_raw=str(ROOT/'assets/skin-response-experiment/skin-zonal-roughness.png');im.file_format='PNG';im.save()
 lk.new(p.outputs['BSDF'],output.inputs['Surface']);lk.new(t.outputs['Color'],p.inputs['Roughness']);ns.remove(emit);ns.remove(co);b.data.color_attributes.remove(attr)
 im.pack();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/skin-response-candidate.blend'),compress=True)
s.cycles.samples=128;s.cycles.use_denoising=False;s.render.resolution_x=800;s.render.resolution_y=978;s.render.filepath=str(ROOT/'renders/skin-response-experiment'/('skin-'+mode+'.png'));bpy.ops.render.render(write_still=True)
