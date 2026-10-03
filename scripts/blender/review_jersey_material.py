"""Compare portable jersey maps against the working source, without overwrite."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];mode=a[0] if a else 'new'
s=bpy.context.scene
if mode in ['new','fine']:
 m=bpy.data.materials['CottonCharcoal'];ns=m.node_tree.nodes;lk=m.node_tree.links;p=next(n for n in ns if n.type=='BSDF_PRINCIPLED')
 co=ns.new('ShaderNodeTexCoord');mapping=ns.new('ShaderNodeMapping');mapping.vector_type='POINT';mapping.inputs['Scale'].default_value=((220,220,1) if mode=='fine' else (55,55,1));lk.new(co.outputs['UV'],mapping.inputs['Vector'])
 for filename,socket,cs in [('jersey-color.png','Base Color','sRGB'),('jersey-roughness.png','Roughness','Non-Color'),('jersey-normal.png','Normal','Non-Color')]:
  t=ns.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'assets/cloth-experiment'/filename),check_existing=True);t.image.colorspace_settings.name=cs;lk.new(mapping.outputs['Vector'],t.inputs['Vector'])
  if socket=='Normal':
   nm=ns.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.3 if mode=='fine' else .6;lk.new(t.outputs['Color'],nm.inputs['Color']);lk.new(nm.outputs['Normal'],p.inputs[socket])
  else:lk.new(t.outputs['Color'],p.inputs[socket])
 # Keep the seam on a separate plain material since its original mesh lacks UVs.
 seam=bpy.data.objects.get('CollarRibbing')
 if seam:
  sm=bpy.data.materials.new('CollarCottonPlain');sm.use_nodes=True;sp=sm.node_tree.nodes.get('Principled BSDF');sp.inputs['Base Color'].default_value=(.024,.025,.026,1);sp.inputs['Roughness'].default_value=.86;seam.data.materials.clear();seam.data.materials.append(sm)
 for im in bpy.data.images:
  if im.source=='FILE':
   try:im.pack()
   except:pass
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('scenes/jersey-material-'+mode+'.blend')),compress=True)
# Chest crop, keep same lights and direction to measure material rather than lighting.
c=s.camera;target=Vector((0,-.045,1.23));c.location=(.06,-.82,1.37);c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=90
s.render.resolution_x=900;s.render.resolution_y=800;s.cycles.samples=96;s.cycles.use_denoising=False;s.render.filepath=str(ROOT/'renders/cloth-experiment'/('jersey-'+mode+'.png'));bpy.ops.render.render(write_still=True)
