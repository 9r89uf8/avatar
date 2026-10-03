"""Recreate pinned CC0 dependencies. Run with Python 3 from the repository root.

Assets retain original authors/licenses. This only downloads source inputs; it does
not install system-wide tools or publish anything. See licenses/ and source manifest.
"""
import hashlib,json,subprocess,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];vendor=ROOT/'vendor';vendor.mkdir(exist_ok=True)
commit='afb9f530a7c2741dedb8df0ebae2e0b183caec21'
repo=vendor/'mpfb2'
if not repo.exists():subprocess.run(['git','clone','https://github.com/makehumancommunity/mpfb2.git',str(repo)],check=True)
subprocess.run(['git','-C',str(repo),'checkout',commit],check=True)
manifest=json.loads((ROOT/'config/source-downloads.json').read_text())
# The manifest records complete original evidence. Its pack list is intentionally
# read as data, with direct URLs and hashes locked by the build.
packs=manifest.get('packs',manifest.get('asset_packs',[])) if isinstance(manifest,dict) else manifest
if not packs:raise RuntimeError('No packs in source manifest; inspect config/source-downloads.json')
for pack in packs:
 url=pack.get('download_url') or pack.get('url')
 if not url:raise RuntimeError('Missing download URL')
 dest=vendor/'downloads'/url.rsplit('/',1)[-1];dest.parent.mkdir(exist_ok=True)
 if not dest.exists():urllib.request.urlretrieve(url,dest)
 expected=pack.get('sha256')
 if expected and hashlib.sha256(dest.read_bytes()).hexdigest()!=expected:raise RuntimeError('Checksum mismatch: '+str(dest))
 with zipfile.ZipFile(dest) as z:
  for name in z.namelist():
   candidate=(vendor/'assets'/name).resolve()
   if not candidate.is_relative_to((vendor/'assets').resolve()):raise RuntimeError('Unsafe archive member')
  z.extractall(vendor/'assets')
print('Assets recreated. Run the documented Blender build next.')
