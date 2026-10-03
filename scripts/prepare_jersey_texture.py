"""Author a seamless, synthetic jersey stitch tile. No photographic claims."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'assets/cloth-experiment';out.mkdir(exist_ok=True)
N=512
# Four loops wide and four rows tall per tile. Each pair of diagonal yarns
# forms the characteristic V rib. Low-frequency fiber irregularity is periodic.
y,x=np.mgrid[0:N,0:N]/N;u=x*4;v=y*4
phase=(v%1);s=u-np.floor(u)-.5
# Each half follows one knitted leg; subtle periodic height variability avoids
# an unbroken machined line. This is a material approximation, not measured cloth.
left=np.exp(-((s-(-.39+.32*phase))/.085)**2)
right=np.exp(-((s-(.39-.32*phase))/.085)**2)
ends=np.sin(np.pi*phase)**.6
h=(left+right)*ends
h*=.88+.06*np.sin(2*np.pi*(x*17+y*13))+.045*np.sin(2*np.pi*(x*37-y*31))
h+=.018*np.sin(2*np.pi*x*117)*np.sin(2*np.pi*y*103)
# Numerical normal slope at restrained height. Actual UV scale is documented
# by the Blender material; use a weak bump for cotton, not embossed leather.
dx=(np.roll(h,-1,1)-np.roll(h,1,1))*N/8
dy=(np.roll(h,-1,0)-np.roll(h,1,0))*N/8
n=np.stack([-dx*.045,-dy*.045,np.ones_like(h)],axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
Image.fromarray(np.uint8((n*.5+.5)*255)).save(out/'jersey-normal.png')
fiber=.90+.07*h+.014*np.sin(2*np.pi*(x*41+y*19))
# Linear base color .028 -> about sRGB .183, lightly varied per yarn.
linear=np.stack([fiber*.028,fiber*.029,fiber*.03],axis=-1)
srgb=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)
Image.fromarray(np.uint8(np.clip(srgb,0,1)*255)).save(out/'jersey-color.png')
r=np.clip(.84-.035*h+.01*np.sin(2*np.pi*(x*7+y*9)),0,1)
Image.fromarray(np.uint8(r*255)).save(out/'jersey-roughness.png')
(out/'PROVENANCE.json').write_text(json.dumps({'source':'Project-authored analytic periodic stitch approximation','photographic_or_scanned':False,'mapResolution':N,'loopsPerTile':[4,4],'normalConvention':'OpenGL +Y','license':'Project-authored asset'},indent=2))
print(out)
