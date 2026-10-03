"""Restrained anatomical medium-scale relief, separate from pore normal detail.

This is a small authored corrective, not inferred scan geometry. Magnitudes are
submillimetric and deliberately preserve the established skin topology and UVs.
"""
import bpy,math
from mathutils import Vector

def refine_face_surface(body):
    keys=body.data.shape_keys.key_blocks;basis=keys[0]
    mixed=body.shape_key_add(name='_current_face_sample',from_mix=True)
    positions=[p.co.copy() for p in mixed.data];body.shape_key_remove(mixed)
    target=body.shape_key_add(name='FaceSurfaceRefine',from_mix=False)
    affected=0
    for index,p in enumerate(positions):
        x,y,z=p;dy=0.;dz=0.
        if y<-.086 and 1.375<z<1.515:
            # Shallow nasolabial valley and adjacent soft cheek volume. It is
            # strongest near the alar root and fades before the mouth corner.
            t=(1.458-z)/.044
            if 0<t<1:
                line=.017+.012*t-.002*math.sin(math.pi*t)
                d=abs(x)-line;fade=math.sin(math.pi*t)**.8
                dy+=.00036*math.exp(-(d/.0026)**2)*fade
                dy-=.00042*math.exp(-((d-.006)/.0065)**2)*fade
            # Lower-lid transition follows the orbital curve, not a straight band.
            ex=abs(x)-.0292
            if abs(ex)<.019:
                fold=1.4768+.004*(ex/.019)**2
                dz0=z-fold
                dy+=.00020*math.exp(-(dz0/.0016)**2)*math.exp(-(ex/.016)**4)
                dy-=.00026*math.exp(-((dz0+.003)/.0038)**2)*math.exp(-(ex/.016)**4)
            # Very small lower-lip/chin transition to give the oral region a
            # readable plane change under oblique lighting.
            dy+=.00025*math.exp(-((z-1.398)/.0035)**2)*math.exp(-(x/.019)**4)
            # Purposeful soft-tissue asymmetry, under half a millimetre.
            if x>0:dy-=.00022*math.exp(-((x-.043)/.012)**2-((z-1.456)/.017)**2)
        if abs(dy)>1e-7:affected+=1
        target.data[index].co=basis.data[index].co+Vector((0,dy,dz))
    target.value=1.;body['faceSurfaceRefinement']='Authored sub-mm orbital and nasolabial relief; not a scan.'
    print('FACE_SURFACE_REFINED',affected,flush=True)
