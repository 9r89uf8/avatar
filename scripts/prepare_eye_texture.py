"""Tune the CC0 iris hue to neutral brown while preserving radial fiber detail."""
from PIL import Image
import numpy as np
from pathlib import Path
import argparse
parser=argparse.ArgumentParser();parser.add_argument("--gain",type=float,default=1.0);parser.add_argument("--output",default="assets/textures/eye-brown-natural.png");args=parser.parse_args()
if not .25 <= args.gain <= 3:parser.error("gain must be between .25 and 3")
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'vendor/assets/eyes/materials/brown_eye.png'
rgba=np.asarray(Image.open(p).convert('RGBA'),dtype=np.float32)/255
a=rgba[...,:3].copy()
# Only strongly red-dominant iris pixels change. Sclera and veins remain untouched.
r,g,b=a[...,0],a[...,1],a[...,2]
w=np.clip((r-g-.10)*8,0,1)*np.clip((r-b-.12)*8,0,1)
luma=(r*.2126+g*.7152+b*.0722)
# Low-chroma warm brown, varying luminance retained from original fibers.
target=np.stack([luma*.80,luma*.68,luma*.54],axis=-1)*args.gain
a=a*(1-w[...,None])+target*w[...,None]
out=ROOT/args.output;out.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(np.uint8(np.concatenate([np.clip(a,0,1),rgba[...,3:4]],axis=-1)*255),'RGBA').save(out)
print(out)
