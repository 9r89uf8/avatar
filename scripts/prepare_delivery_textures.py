"""Create explicit browser texture derivatives without altering source maps."""
from pathlib import Path
from PIL import Image
import json,hashlib
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'assets/textures';out=ROOT/'assets/delivery';out.mkdir(parents=True,exist_ok=True)
items=[]
skin_source='skin-reference-clean-lids.png' if (src/'skin-reference-clean-lids.png').exists() else 'skin-reference-soft.png'
for name,target,maxsize,mode in [(skin_source,'skin-color.jpg',2048,'RGB'),('skin-normal.png','skin-normal.png',2048,'RGB'),('skin-roughness.png','skin-roughness.png',2048,'L'),('eye-brown-natural.png','eye-brown-natural.png',1024,'RGBA')]:
 p=src/name
 if not p.exists():continue
 im=Image.open(p).convert(mode);im.thumbnail((maxsize,maxsize),Image.Resampling.LANCZOS)
 kwargs={'quality':94,'subsampling':0} if target.endswith('.jpg') else {'optimize':True}
 dest=out/target;im.save(dest,**kwargs);items.append({'source':str(p.relative_to(ROOT)),'output':str(dest.relative_to(ROOT)),'size':list(im.size),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(ROOT/'reports/delivery-textures.json').write_text(json.dumps(items,indent=2));print(json.dumps(items,indent=2))
