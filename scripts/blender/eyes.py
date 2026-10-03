"""Stable coated-eye shading while retaining editable anatomical eye layers."""
import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
def refine_eyes(eyes,rig):
    # MakeHuman high-poly eyes already contain two layers: a recessed textured
    # eyeball and a slightly larger clear shell. The source atlas marks shell
    # faces with alpha=0; preserve that semantic rather than duplicating globes.
    image=bpy.data.images.load(str(ROOT/'vendor/assets/eyes/materials/brown_eye.png'),check_existing=True)
    w,h=image.size;pixels=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4)
    m=bpy.data.materials.new('CorneaOptical');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1,1,1,1);p.inputs['Roughness'].default_value=.018;p.inputs['IOR'].default_value=1.376;p.inputs['Transmission Weight'].default_value=0;p.inputs['Alpha'].default_value=0
    shell_index=len(eyes.data.materials);eyes.data.materials.append(m)
    uv=eyes.data.uv_layers.active.data;count=0
    for face in eyes.data.polygons:
        center=sum((uv[i].uv for i in face.loop_indices),Vector((0,0)))/len(face.loop_indices)
        alpha=pixels[min(h-1,max(0,int(center.y*h))),min(w-1,max(0,int(center.x*w))),3]
        if alpha<.5:face.material_index=shell_index;count+=1
    for mat in eyes.data.materials:
        if mat.name=='CorneaOptical':continue
        for n in mat.node_tree.nodes:
            if n.type=='BSDF_PRINCIPLED':n.inputs['Coat Weight'].default_value=.8;n.inputs['Coat Roughness'].default_value=.035;n.inputs['Coat IOR'].default_value=1.376;n.inputs['Roughness'].default_value=.31;n.inputs['Specular IOR Level'].default_value=.25
    # Avoid a non-caustic shadow estimator blacking out the inner iris.
    # Lids still cast natural shadows; this only suppresses eye self-shadow.
    eyes.visible_shadow=False
    eyes['opticalShellFaceCount']=count
    eyes['eyeShadingStrategy']='Coated opaque iris/sclera. Anatomical outer shell retained but alpha=0. Physical transmission disabled after comparative visual test.'
    print('CORNEA_LAYER_FACES',count,flush=True)
    return eyes
