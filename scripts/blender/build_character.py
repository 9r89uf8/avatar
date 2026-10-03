"""Repeatable adult character build. Run from Blender 4.3+ background mode."""
import bpy,sys,math,json,os,argparse,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
for directory in ['scenes','renders','reports','exports','.runtime/blender']:(ROOT/directory).mkdir(parents=True,exist_ok=True)
arguments=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=256);parser.add_argument('--no-render',action='store_true');options=parser.parse_args(arguments)
from bootstrap import load_mpfb
mpfb=load_mpfb()
from bl_ext.avatar.mpfb.services.humanservice import HumanService
from bl_ext.avatar.mpfb.services.targetservice import TargetService
from bl_ext.avatar.mpfb.services.locationservice import LocationService
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
macro=TargetService.get_default_macro_info_dict();macro.update({'gender':0.0,'age':0.5,'muscle':0.35,'weight':0.43,'height':0.5,'proportions':0.5});macro['race']={'caucasian':0.75,'asian':0.15,'african':0.1}
human=HumanService.create_human(macro_detail_dict=macro);human.name='AvatarBody'
# Neutral adult reference proportions: oval cheeks, softly tapered jaw, full lower lip.
targets={'head/head-oval':0.28,'head/head-scale-horiz-incr':0.08,'head/head-fat-incr':0.08,'chin/chin-width-decr':0.28,'chin/chin-height-decr':0.10,'nose/nose-scale-horiz-incr':0.10,'nose/nose-scale-vert-incr':0.06,'mouth/mouth-scale-horiz-incr':0.17,'mouth/mouth-upperlip-volume-decr':0.08,'mouth/mouth-trans-up':0.10,'eyes/l-eye-eyefold-concave':0.12,'eyes/r-eye-eyefold-concave':0.10,'cheek/l-cheek-bones-incr':0.08,'cheek/r-cheek-bones-incr':0.10,'asym/asym-jaw-1-l':0.05}
troot=Path(LocationService.get_mpfb_data('targets'))
for path,value in targets.items():
 p=troot/(path+'.target.gz')
 if p.exists():TargetService.load_target(human,str(p),weight=value)
from surface_forms import refine_face_surface
refine_face_surface(human)
rig=HumanService.add_builtin_rig(human,'default');rig.name='AvatarRig'
# Anatomy and clothing assets are official/community CC0; see sources manifest.
def asset(subdir,slug,typ,levels=1):
 p=ROOT/'vendor/assets'/subdir/slug/(slug+'.mhclo')
 if not p.exists():raise FileNotFoundError(p)
 ob=HumanService.add_mhclo_asset(str(p),human,asset_type=typ,subdiv_levels=levels,material_type='GAMEENGINE');return ob
HumanService.set_character_skin(str(ROOT/'vendor/assets/skins/young_caucasian_female2/young_caucasian_female2.mhmat'),human,skin_type='GAMEENGINE')
eyes=asset('eyes','high-poly','Eyes');eyes.name='Eyes'
brows=asset('eyebrows','mindfront_eyebrows_02','Eyebrows',0);brows.name='Brows'
lashes=asset('eyelashes','mindfront_eyelashes_01','Eyelashes',0);lashes.name='Lashes'
teeth=asset('teeth','teeth_base','Teeth');teeth.name='Teeth'
tongue=asset('tongue','tongue01','Tongue');tongue.name='Tongue'
cover=asset('clothes','joepal_crude_t-shirt_female','Clothes');bpy.data.objects.remove(cover,do_unlink=True)
shirt=asset('clothes','toigo_basic_tucked_t-shirt','Clothes');shirt.name='CharcoalTee'
pants=asset('clothes','toigo_wool_pants','Clothes');pants.name='Trousers'
shoes=asset('clothes','shoes02','Clothes');shoes.name='Shoes'
hair=asset('hair','long01','Hair');hair.name='Hair'
# Use a single Principled surface for predictable glTF PBR export.
def principled(mat):
 for n in mat.node_tree.nodes:
  if n.type=='BSDF_PRINCIPLED':return n
 raise ValueError(mat.name)
for ob in [human,eyes,brows,lashes,shirt,pants,shoes,hair]:
 for poly in ob.data.polygons:poly.use_smooth=True
 for mat in ob.data.materials:
  try:p=principled(mat)
  except ValueError:continue
  if ob==human:
   mat.name='Skin';p.inputs['Roughness'].default_value=.48;p.inputs['Subsurface Weight'].default_value=.12;p.inputs['Subsurface Radius'].default_value=(1,.4,.22);p.inputs['Subsurface Scale'].default_value=.008;p.inputs['IOR'].default_value=1.4
   # Fine irregular microrelief has real-world scale. 0.07mm range, no gravel.
   n=mat.node_tree.nodes;lk=mat.node_tree.links
   tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=1200;tex.inputs['Detail'].default_value=2.3;tex.inputs['Roughness'].default_value=.7
   co=n.new('ShaderNodeTexCoord');lk.new(co.outputs['Object'],tex.inputs['Vector'])
   bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.000065;lk.new(tex.outputs['Fac'],bump.inputs['Height']);lk.new(bump.outputs['Normal'],p.inputs['Normal'])
   normal_path=ROOT/'assets/textures/skin-normal.png'
   if normal_path.exists():
    normal_tex=n.new('ShaderNodeTexImage');normal_tex.image=bpy.data.images.load(str(normal_path),check_existing=True);normal_tex.image.colorspace_settings.name='Non-Color'
    normal=n.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.8;lk.new(normal_tex.outputs['Color'],normal.inputs['Color']);lk.new(normal.outputs['Normal'],p.inputs['Normal'])
   rough_path=ROOT/'assets/textures/skin-roughness.png'
   if rough_path.exists():
    rt=n.new('ShaderNodeTexImage');rt.image=bpy.data.images.load(str(rough_path),check_existing=True);rt.image.colorspace_settings.name='Non-Color';lk.new(rt.outputs['Color'],p.inputs['Roughness'])
   photo=ROOT/'assets/textures/skin-reference-clean-lids.png'
   if not photo.exists():photo=ROOT/'assets/textures/skin-reference-soft.png'
   if not photo.exists():photo=ROOT/'assets/textures/skin-reference-color.png'
   if photo.exists():
    for imnode in n:
     if imnode.type=='TEX_IMAGE' and imnode.image and imnode.image.colorspace_settings.name=='sRGB':imnode.image=bpy.data.images.load(str(photo),check_existing=True)
  elif ob==eyes:
   mat.name='EyeSurface';p.inputs['Roughness'].default_value=.27;p.inputs['Coat Weight'].default_value=.9;p.inputs['Coat Roughness'].default_value=.025;p.inputs['Coat IOR'].default_value=1.376
   for n in mat.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
     n.image=bpy.data.images.load(str(ROOT/'assets/textures/eye-brown-natural.png') if (ROOT/'assets/textures/eye-brown-natural.png').exists() else str(ROOT/'vendor/assets/eyes/materials/brown_eye.png'),check_existing=True)
  elif ob in [shirt,pants,shoes]:
   mat.name={'CharcoalTee':'CottonCharcoal','Trousers':'WoolCharcoal','Shoes':'Leather'}[ob.name]
   for link in list(mat.node_tree.links):
    if link.to_socket in [p.inputs['Base Color'],p.inputs['Alpha']]:mat.node_tree.links.remove(link)
   p.inputs['Base Color'].default_value=(.028,.029,.03,1) if ob==shirt else (.021,.025,.032,1)
   p.inputs['Roughness'].default_value=.84 if ob!=shoes else .45
   p.inputs['Sheen Weight'].default_value=.2 if ob!=shoes else 0
  elif ob==hair:
   mat.name='HairDarkBrown';p.inputs['Roughness'].default_value=.47
from eyes import refine_eyes
cornea=refine_eyes(eyes,rig)
from cloth import refine_clothing
refine_clothing(shirt,rig)
# Keep expression targets explicit, portable and independent of modeling morphs.
for name in ['eyeBlinkLeft','eyeBlinkRight','mouthSmileLeft','mouthSmileRight','jawOpen','browInnerUp']:
 TargetService.load_target(human,str(ROOT/'vendor/assets/targets/faceunits'/(name+'.target')),weight=0)
from facial import transfer_face_targets
transfer_face_targets(human,[lashes,brows],['eyeBlinkLeft','eyeBlinkRight','browInnerUp'])
from eyelids import build_eyelids
lid_objects,lid_stats=build_eyelids()
# Subdivision for portrait source. Export will preserve morph correspondence deliberately.
sub=human.modifiers.new('PortraitSubdivision','SUBSURF');sub.levels=1;sub.render_levels=2
# Relax arms without introducing facial deformation.
from mathutils import Quaternion
for name,angle in [('upperarm01.L',math.radians(30)),('upperarm01.R',math.radians(-30))]:
 if name in rig.pose.bones:
  bone=rig.pose.bones[name];bone.rotation_mode='QUATERNION'
  local_axis=bone.bone.matrix_local.to_3x3().inverted()@Vector((0,1,0))
  bone.rotation_quaternion=Quaternion(local_axis,angle)
# Build contact locks only after the final body pose and cloth modifiers exist.
bpy.context.view_layer.update()
from groom import build_groom
groom_objects=build_groom(human,rig,hair)
# Fixed review scene, meter scale, soft neutral area lighting.
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
scene.world.color=(.14,.14,.14);scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.28,.32,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
bounds=[human.matrix_world@Vector(x) for x in human.bound_box];zmax=max(p.z for p in bounds)
look=Vector((0,-.015,zmax-.185))
def point(ob,p):ob.rotation_euler=(Vector(p)-ob.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;point(o,look)
area('Key',(-1.3,-2.0,2.55),175,1.5,(1,.92,.86));area('Fill',(1.6,-.7,1.9),60,1.4,(.81,.88,1));area('Rim',(.3,.9,2.15),35,1,(1,.9,.8))
camd=bpy.data.cameras.new('PortraitCamera');cam=bpy.data.objects.new('PortraitCamera',camd);scene.collection.objects.link(cam);cam.location=(0,-1.10,zmax-.105);point(cam,look);camd.lens=90;scene.camera=cam
bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,0));floor=bpy.context.object;floor.name='StudioFloor';floor['avatar_exclude_export']=True
fm=bpy.data.materials.new('StudioFloor');fm.use_nodes=True;fp=fm.node_tree.nodes.get('Principled BSDF');fp.inputs['Base Color'].default_value=(.055,.06,.065,1);fp.inputs['Roughness'].default_value=1;floor.data.materials.append(fm)
scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.55
try:
 import addon_utils;addon_utils.enable('cycles');scene.render.engine='CYCLES';scene.cycles.samples=options.samples;scene.cycles.use_denoising=False
except Exception as e:
 print('CYCLES_UNAVAILABLE',e);scene.render.engine='BLENDER_EEVEE_NEXT'
for image in bpy.data.images:
 if image.source=='FILE':
  try:image.pack()
  except:pass
scene.render.filepath=str(ROOT/'renders/portrait-baseline.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scenes/avatar-master.blend'),compress=True)
inv={'height':zmax,'objects':[{'name':o.name,'type':o.type,'verts':len(o.data.vertices) if o.type=='MESH' else 0,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []} for o in scene.objects],'bones':[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones],'morphs':[k.name for k in human.data.shape_keys.key_blocks]}
(ROOT/'reports/source-inventory.json').write_text(json.dumps(inv,indent=2))
print('BUILD_SAVED',str(ROOT/'scenes/avatar-master.blend'), 'HEIGHT',zmax,'RENDER',scene.render.engine,flush=True)
if not options.no_render:
 bpy.ops.render.render(write_still=True)
 Path(scene.render.filepath).with_suffix('.json').write_text(json.dumps({'type':'Editable source rendered in Blender Cycles','sourceBlendSha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'imageSha256':hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest(),'view':'portrait','expression':'neutral','samples':options.samples},indent=2))
