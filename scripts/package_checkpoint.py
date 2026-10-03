"""Package a hash-checked WIP revision without replacing historical/Library files."""
from pathlib import Path
from datetime import datetime,timezone
import zipfile,json,hashlib,shutil,argparse,re,os
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args()
if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,32}',a.revision):p.error('Use a short lowercase revision name, not a path.')
out=ROOT/'deliverables'/a.revision;out.mkdir(parents=True,exist_ok=True)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
model=ROOT/'exports/avatar-uncompressed.glb';blend=ROOT/'scenes/avatar-master.blend';modelsha=sha(model);blendsha=sha(blend)
assert sha(ROOT/'web/public/assets/avatar.glb')==modelsha,'Public model differs'
assert json.loads((ROOT/'web/public/assets/avatar.web.json').read_text())['glbSha256']==modelsha,'Sidecar hash differs'
validation=json.loads((ROOT/'reports/gltf-validation.json').read_text())
assert validation['sha256']==modelsha and validation['validator']['issues']['numErrors']==0 and not validation['contractIssues'],'GLB validation is stale or failed'
source=json.loads((ROOT/'reports/source-reopened.json').read_text())
assert source['sourceSha256']==blendsha and not source['missingFiles'] and all(i['packed'] for i in source['images']),'Source inspection is stale/incomplete'
cloth=json.loads((ROOT/'reports/cloth-export-parity.json').read_text());assert cloth['glbSha256']==modelsha and cloth['passed'],'Cloth parity is stale/failed'
hair=json.loads((ROOT/'reports/groom/runtime-hair-contact.json').read_text());assert hair['sourceSha256']==blendsha and not any(s['penetrating_vertices'] for s in hair['scenarios']),'Hair contact evidence is stale/failed'
for artifact in out.iterdir():
 if artifact.is_file() and hasattr(os,'listxattr') and 'user.library-file-id' in os.listxattr(artifact):raise RuntimeError('Library-backed revision exists; use the Library update workflow or a new revision.')
test_report=(ROOT/'web/reports/unit-tests.txt').read_text();test_counts=re.findall(r'\btests\s+(\d+)',test_report);fail_counts=re.findall(r'\bfail\s+(\d+)',test_report);assert test_counts and fail_counts and int(fail_counts[-1])==0,'Unit-test report is incomplete/failed';test_count=int(test_counts[-1])
manifest={'createdAt':datetime.now(timezone.utc).isoformat(),'revision':a.revision,'status':'Work in progress. Technical checkpoint; not ultrarealistic, not user-approved, browser appearance/performance unverified.','sourceBlendSha256':blendsha,'glbSha256':modelsha,'files':[],'validation':{'gltfErrors':0,'gltfWarnings':validation['validator']['issues']['numWarnings'],'sourceImagesPacked':len(source['images']),'hairContactScenarios':len(hair['scenarios']),'tests':test_count,'browserVerified':False}}
webzip=out/'Avatar browser WIP.zip'
with zipfile.ZipFile(webzip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for item in (ROOT/'web').rglob('*'):
  if item.is_file() and not any(part in ['node_modules','dist','.git'] for part in item.relative_to(ROOT/'web').parts):z.write(item,'avatar-studio/'+str(item.relative_to(ROOT/'web')))
 for src,name in [('docs/quality-status.md','QUALITY-STATUS.md'),('licenses/ASSET-CREDITS.md','ASSET-CREDITS.md'),('docs/next-source-handoff.md','NEXT-STEP.md')]:z.write(ROOT/src,'avatar-studio/'+name)
sourcezip=out/'Avatar source pipeline WIP.zip'
with zipfile.ZipFile(sourcezip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for directory in ['scripts','config','docs','licenses']:
  for item in (ROOT/directory).rglob('*'):
   if item.is_file() and '__pycache__' not in item.parts:z.write(item,str(item.relative_to(ROOT)))
 for directory in ['assets/textures','assets/groom','assets/delivery']:
  for item in (ROOT/directory).rglob('*'):
   if item.is_file():z.write(item,str(item.relative_to(ROOT)))
 for item in ROOT.glob('*.jfif'):z.write(item,item.name)
 for item in ROOT.glob('*.docx'):z.write(item,item.name)
 for name in ['README.md','AGENTS.md','CLAUDE.md','Blender_Avatar_Agent_Toolkit (1).md','Realistic Avatar Build Plan for Codex and Claude Code.md']:z.write(ROOT/name,name)
 names=['source-selection.md','asset-procurement-options.md','alternate-source-assessment.md','visual-iteration-log.md','verification-summary.json','gltf-validation.json','reference-analysis.md','reference-analysis.json','face-projection.json','source-reopened.json','export-inventory.json','cloth-export-parity.json','cloth-export-correction.json','delivery-textures.json','render-evidence.json','fresh-archive-rebuild.json']
 for name in names:
  item=ROOT/'reports'/name
  if item.exists():z.write(item,str(item.relative_to(ROOT)))
 for directory in ['reports/reference-baseline','reports/reference-bake','reports/lid-diffuse-experiment']:
  for item in (ROOT/directory).glob('*'):
   if item.is_file() and item.suffix in ['.json','.md']:z.write(item,str(item.relative_to(ROOT)))
 for name in ['reports/eyelids/rim-correspondence.json','reports/eyelids/README.md','reports/eyelids/blink-cause-assessment.json','reports/groom/root-flow/README.md','reports/groom/runtime-hair-contact.json','reports/groom/root-flow/final-audit.json','reports/fitting/reference-anatomy-v4.npz','reports/fitting/reference-anatomy-v4.json','reports/fitting/README.md','reports/fitting/assessment.json']:
  item=ROOT/name
  if item.exists():z.write(item,name)
 z.writestr('CHECKPOINT.md','''# Work-in-progress source checkpoint\n\nThis contains the selected build pipeline, prepared maps, references and selected evidence. It is not the full temporary experiment archive; unselected experiment renders/scenes/assets are omitted. The separate editable .blend is self-contained and opens without the vendor cache. To use it with review/export scripts, place it at scenes/avatar-master.blend after extraction. Otherwise rebuild through README.md, which downloads pinned original sources and uses the included prepared maps.\n\nThe browser archive is independently runnable using its README. No website has been published. This checkpoint does not meet the requested ultrarealism target, and its browser appearance and hardware smoothness are unverified. See docs/next-source-handoff.md for the proposed substantive next step.\n''')
visualzip=out/'Avatar visual review WIP.zip'
with zipfile.ZipFile(visualzip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for entry in json.loads((ROOT/'reports/render-evidence.json').read_text())['images']:
  item=ROOT/entry['file'];z.write(item,entry['file']);z.write(item.with_suffix('.json'),str(item.with_suffix('.json').relative_to(ROOT)))
 for name in ['reports/render-evidence.json','reports/verification-summary.json','docs/quality-status.md','docs/next-source-handoff.md']:z.write(ROOT/name,name)
 z.writestr('README.txt','Actual source and GLB re-import renders, not browser screenshots. All are WIP and remain visibly synthetic. Start with renders/portrait-baseline.png (current 512-sample source portrait), renders/glb-portrait-refined.png (delivery representation), and the full/profile/blink/head-turn evidence. JSON sidecars bind images to exact source/model hashes. No human approval or real-device performance is asserted.\n')
for src,name in [(blend,'Avatar editable source WIP.blend'),(model,'Avatar model WIP.glb')]:shutil.copy2(src,out/name)
checks=[]
for artifact in [out/'Avatar editable source WIP.blend',out/'Avatar model WIP.glb',webzip,sourcezip,visualzip]:
 manifest['files'].append({'path':str(artifact),'name':artifact.name,'bytes':artifact.stat().st_size,'sha256':sha(artifact)})
 if artifact.suffix=='.zip':
  with zipfile.ZipFile(artifact) as z:
   corrupt=z.testzip();assert corrupt is None,corrupt;checks.append({'file':artifact.name,'entries':len(z.infolist()),'corruptEntry':corrupt})
portrait=out/'Avatar source portrait WIP.png';shutil.copy2(ROOT/'renders/portrait-baseline.png',portrait);manifest['preview']={'path':str(portrait),'name':portrait.name,'bytes':portrait.stat().st_size,'sha256':sha(portrait),'type':'Source Cycles render, not browser screenshot'}
(out/'checkpoint-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'archive-validation.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(manifest,indent=2))
