import './style.css';
import { AvatarViewer } from './viewer';
import { formatCaptureSummary, serializeDiagnostic } from './diagnostics';
import type { FrameCaptureResult } from './diagnostics';
import type { LightPreset, View } from './types';

const icons={
  pause:'<path d="M8 5v14M16 5v14"/>',play:'<path d="m8 5 11 7-11 7z"/>',
  reset:'<path d="M3 10a9 9 0 1 1 1.8 8M3 4v6h6"/>',
  expand:'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/>',
  orbit:'<ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-28 12 12)"/><circle cx="12" cy="12" r="3"/>',
  close:'<path d="m6 6 12 12M18 6 6 18"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/>',
  eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>',
};
const icon=(key:keyof typeof icons)=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[key]}</svg>`;
const app=document.querySelector<HTMLDivElement>('#app')!;
app.innerHTML=`
  <main class="atelier">
    <header class="topbar">
      <a class="wordmark" href="/" aria-label="Atelier home"><span class="mark">a</span>atelier<span class="wordmark-dot">.</span></a>
      <div class="project-label"><span class="tiny-line"></span> DIGITAL HUMAN STUDIES <span class="project-number">/ 001</span></div>
      <button class="text-button about-trigger" id="about" aria-label="About this character study">About the study ${icon('arrow')}</button>
    </header>
    <section class="studio" aria-label="Interactive 3D character studio">
      <div class="studio-wash"></div>
      <div class="vertical-caption" aria-hidden="true">FORM · LIGHT · EXPRESSION</div>
      <div class="canvas-wrap"><canvas id="avatar-canvas" aria-label="3D character. Drag to orbit, scroll to zoom. Use view buttons for portrait and full body." tabindex="0"></canvas><figure id="fallback-poster" hidden><img src="/assets/poster.jpg" alt="Still Cycles render of the current avatar work in progress"/><figcaption>Still render · 3D is unavailable on this device</figcaption></figure></div>
      <div class="introduction">
        <p class="eyebrow"><span class="live-dot"></span> A REAL-TIME CHARACTER STUDY</p>
        <h1>A little<br/>more human.</h1>
        <p class="intro-note">A study in presence.<br/>Explore the details that bring<br/>a digital character to life.</p>
      </div>
      <div class="character-label"><span class="micro-label">CHARACTER 001</span><h2 id="character-name">The portrait study</h2><p id="character-description">Made of geometry. Shaped by light.</p></div>
      <div class="status-pill" id="status"><span class="live-dot"></span><span id="status-text">Preparing the studio</span></div>
      <div class="loading-panel" id="loading" role="status" aria-live="polite"><div class="loading-orbit"></div><p id="loading-title">Bringing the study into focus</p><span id="loading-subtitle">Loading real 3D geometry & materials</span><button id="retry" class="pill-button" hidden>Try again</button></div>
      <div class="view-switch" role="group" aria-label="Camera view"><button class="selected" data-view="portrait" aria-pressed="true">Portrait</button><button data-view="threeQuarter" aria-pressed="false">Three-quarter</button><button data-view="full" aria-pressed="false">Full body</button></div>
      <div class="viewport-tools"><button id="orbit" class="icon-button" title="Slow camera orbit" aria-label="Toggle slow camera orbit" aria-pressed="false">${icon('orbit')}</button><button id="fullscreen" class="icon-button" title="Enter fullscreen" aria-label="Enter fullscreen">${icon('expand')}</button></div>
      <div class="interaction-hint"><span class="drag-icon">↔</span> Drag to explore <span class="hint-dot">·</span> Scroll to get closer</div>
    </section>
    <aside class="controls" aria-label="Character controls">
      <div class="controls-heading"><div><p class="eyebrow">THE SMALL DETAILS</p><h2>Make it feel alive.</h2></div><span class="section-index">01 — 03</span></div>
      <div class="control-grid">
        <section class="control-section expression-section"><div class="section-title"><span>01</span><h3>Expression</h3><button id="blink-once" class="subtle-button">${icon('eye')} Blink</button></div><label class="range-label" for="smile"><span>A hint of a smile</span><output id="smile-value">0%</output></label><input id="smile" type="range" min="0" max="100" value="0" step="1" aria-label="Smile intensity"/><div class="range-extremes"><span>Neutral</span><span>Warm</span></div></section>
        <section class="control-section"><div class="section-title"><span>02</span><h3>Movement</h3><button id="pause" class="subtle-button" aria-pressed="false">${icon('pause')} <span id="pause-label">Pause</span></button></div><label class="range-label" for="head-turn"><span>Head turn</span><output id="head-turn-value">0°</output></label><input id="head-turn" type="range" min="-25" max="25" value="0" step="1" aria-label="Head turn in degrees"/><div class="movement-toggles"><label class="toggle"><input id="idle" type="checkbox" checked/><span class="toggle-track"></span>Idle motion</label><label class="toggle"><input id="hair" type="checkbox" checked/><span class="toggle-track"></span>Hair motion</label></div></section>
        <section class="control-section light-section"><div class="section-title"><span>03</span><h3>Light & texture</h3><button id="reset" class="subtle-button" title="Reset all settings">${icon('reset')} Reset</button></div><div class="light-presets" role="group" aria-label="Lighting preset"><button class="selected" data-light="studio" aria-pressed="true"><i class="light-swatch studio-swatch"></i>Studio</button><button data-light="daylight" aria-pressed="false"><i class="light-swatch daylight-swatch"></i>Daylight</button><button data-light="rim" aria-pressed="false"><i class="light-swatch rim-swatch"></i>Rim</button></div><div class="material-options"><label class="toggle"><input id="skin" type="checkbox" checked/><span class="toggle-track"></span>Skin diffusion</label><select id="quality" aria-label="Render quality"><option value="high">High quality</option><option value="balanced">Balanced</option></select></div></section>
      </div>
    </aside>
    <footer class="footer"><p><span class="live-dot"></span> <span id="backend">WEBGL 2</span><span class="footer-divider">/</span> PHYSICALLY BASED RENDERING</p><button id="technical" class="technical-button"><span id="fps">—</span> FPS<span class="footer-divider">/</span> Scene details ${icon('info')}</button><p class="footer-note">An exploration, in three dimensions.</p></footer>
  </main>
  <dialog id="details-dialog"><button class="dialog-close icon-button" aria-label="Close details">${icon('close')}</button><p class="eyebrow">ATELIER / THE CHARACTER STUDY</p><h2>Presence is in<br/>the details.</h2><p class="dialog-intro">This is an interactive 3D character, rendered live in your browser. Orbit the geometry, explore different light, and test the subtle movements that create presence.</p><div id="scene-details"></div><section class="diagnostic-capture" aria-labelledby="diagnostic-heading"><h3 id="diagnostic-heading">Local diagnostics</h3><p id="diagnostic-help">Observe 10 seconds in the current view. Your settings stay unchanged. The JSON includes browser-reported graphics information, asset identity, and measured frame intervals. It stays on this device.</p><div class="diagnostic-actions"><button id="capture-diagnostics" class="pill-button" disabled>Capture 10 seconds</button><button id="cancel-diagnostics" class="pill-button secondary" hidden>Cancel</button><a id="download-diagnostics" class="pill-button" hidden download>Save JSON</a></div><p id="diagnostic-status" role="status" aria-live="polite">Available after live 3D loads.</p></section><p class="dialog-note">Drag to orbit · Shift + drag to pan · Scroll to zoom<br/>1 Portrait · 2 Three-quarter · 3 Full body · Space Pause · R Reset</p></dialog>
  <div id="toast" role="status" aria-live="polite"></div>`;

const $=<T extends HTMLElement=HTMLElement>(selector:string)=>document.querySelector<T>(selector)!;
let viewer:AvatarViewer|null=null;
let toastTimer:ReturnType<typeof setTimeout>;
let diagnosticDownloadUrl:string|null=null;
let sceneFailure:string|null=null;
let initializationGeneration=0;
let diagnosticProgressSecond=-1;
function toast(text:string){$('#toast').textContent=text;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3300);}
function selectButtons(attribute:string,value:string){document.querySelectorAll<HTMLButtonElement>(`[${attribute}]`).forEach(button=>{const selected=button.getAttribute(attribute)===value;button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));});}
function syncPause(){if(sceneFailure||!viewer?.stats.ready)return;const paused=viewer?.state.paused??false;$('#pause').setAttribute('aria-pressed',String(paused));$('#pause').innerHTML=`${icon(paused?'play':'pause')} <span id="pause-label">${paused?'Resume':'Pause'}</span>`;$('#status-text').textContent=paused?'Still, for a moment':'Live in your browser';}
function resetUI(){if(!viewer)return;viewer.reset();$('#smile-value').textContent='0%';$<HTMLInputElement>('#smile').value='0';$('#head-turn-value').textContent='0°';$<HTMLInputElement>('#head-turn').value='0';['idle','hair','skin'].forEach(id=>$<HTMLInputElement>(`#${id}`).checked=true);$<HTMLSelectElement>('#quality').value='high';selectButtons('data-view','portrait');selectButtons('data-light','studio');$('#orbit').setAttribute('aria-pressed','false');syncPause();}
function openDetails(){const stats=viewer?.getInventory();const list=sceneFailure?[['Live 3D','Unavailable'],['Reason',sceneFailure],['Displayed image','Labeled still render; no live frame rate is claimed']]:stats?.ready?[
  ['Renderer','Babylon.js · WebGL 2'],['Geometry',`${Math.round(stats.triangles).toLocaleString()} triangles · ${stats.meshes} meshes`],['Materials',`${stats.materials.length} PBR materials`],['Expression targets',stats.morphTargets.join(', ')||'None in this asset'],['Asset','Real GLB mesh / editable Blender source'],
]:[['Renderer','Preparing the 3D scene']];$('#scene-details').replaceChildren(...list.map(([title,value])=>{const row=document.createElement('div');row.className='detail-row';const dt=document.createElement('span');dt.textContent=title;const dd=document.createElement('strong');dd.textContent=value;row.append(dt,dd);return row;}));if(stats?.warnings.length){const warning=document.createElement('p');warning.className='diagnostic-warning';warning.textContent=stats.warnings.join(' · ');$('#scene-details').append(warning);}$('.dialog-intro').textContent=sceneFailure?'Live 3D is currently unavailable. The viewport shows a labeled still render. You can save a local readiness report with the observed error.':'This is an interactive 3D character, rendered live in your browser. Orbit the geometry, explore different light, and test the subtle movements that create presence.';$<HTMLDialogElement>('#details-dialog').showModal();}
function enableLiveControls(enabled:boolean){document.querySelectorAll<HTMLInputElement|HTMLButtonElement|HTMLSelectElement>('.controls input, .controls button, .controls select, [data-view], #orbit').forEach(control=>control.disabled=!enabled);}
function releaseDiagnosticDownload(){if(diagnosticDownloadUrl){URL.revokeObjectURL(diagnosticDownloadUrl);diagnosticDownloadUrl=null;}$<HTMLAnchorElement>('#download-diagnostics').removeAttribute('href');$<HTMLAnchorElement>('#download-diagnostics').hidden=true;}
function showDiagnosticReport(report:Record<string,unknown>,autoDownload=false){
  releaseDiagnosticDownload();
  diagnosticDownloadUrl=URL.createObjectURL(new Blob([serializeDiagnostic(report)],{type:'application/json'}));
  const link=$<HTMLAnchorElement>('#download-diagnostics');link.href=diagnosticDownloadUrl;link.download=`atelier-diagnostics-${new Date().toISOString().replace(/[:.]/g,'-')}.json`;link.hidden=false;
  $<HTMLButtonElement>('#cancel-diagnostics').hidden=true;
  $<HTMLButtonElement>('#capture-diagnostics').disabled=false;
  $('#capture-diagnostics').textContent=sceneFailure?'Save readiness report':'Capture 10 seconds';
  const sample=report.sample as FrameCaptureResult|undefined;
  $('#diagnostic-status').textContent=sample?formatCaptureSummary(sample):'Live 3D is unavailable. This report contains the observed error and browser information; no FPS or rendering success is claimed.';
  if(autoDownload)link.click();
}
function localReadinessReport():Record<string,unknown>{
  return{schemaVersion:1,reportType:'avatar-local-readiness-diagnostics',createdAt:new Date().toISOString(),status:'unavailable',reason:sceneFailure??'Live 3D has not loaded.',liveSceneLoaded:false,display:'Explicitly labeled still-render fallback',browser:{userAgent:navigator.userAgent,logicalProcessors:navigator.hardwareConcurrency??null,devicePixelRatio:window.devicePixelRatio,reducedMotionPreference:reducedMotion.matches},engineObservation:viewer?.getDiagnosticSnapshot()??null,sample:null,limitations:['No live frame-rate, renderer success or visual-quality approval is claimed.','Unavailable renderer information is left null rather than inferred from the device or user-agent.'],privacy:'Generated and downloaded locally at your request. No telemetry or additional network requests.'};
}
$('#capture-diagnostics').addEventListener('click',()=>{
  if(sceneFailure){showDiagnosticReport(localReadinessReport(),true);return;}
  if(!viewer?.stats.ready){$('#diagnostic-status').textContent='Wait for live 3D to finish loading.';return;}
  try{viewer.captureDiagnostics();$<HTMLButtonElement>('#capture-diagnostics').disabled=true;$<HTMLButtonElement>('#cancel-diagnostics').hidden=false;diagnosticProgressSecond=-1;}
  catch(error){$('#diagnostic-status').textContent=error instanceof Error?error.message:'Diagnostics could not start.';}
});
$('#cancel-diagnostics').addEventListener('click',()=>viewer?.cancelDiagnosticCapture());
$<HTMLDialogElement>('#details-dialog').addEventListener('close',()=>viewer?.cancelDiagnosticCapture('details-closed'));
window.addEventListener('pagehide',()=>{initializationGeneration++;viewer?.dispose();viewer=null;releaseDiagnosticDownload();clearTimeout(toastTimer);});
window.addEventListener('pageshow',event=>{if(event.persisted)void initialize();});
function setView(view:View){viewer?.setView(view);selectButtons('data-view',view);}
$('#about').addEventListener('click',openDetails);$('#technical').addEventListener('click',openDetails);
$('.dialog-close').addEventListener('click',()=>$<HTMLDialogElement>('#details-dialog').close());
$<HTMLDialogElement>('#details-dialog').addEventListener('click',event=>{if(event.target===$('#details-dialog'))$<HTMLDialogElement>('#details-dialog').close();});
$<HTMLInputElement>('#smile').addEventListener('input',event=>{const value=Number((event.target as HTMLInputElement).value);if(viewer)viewer.state.smile=value/100;$('#smile-value').textContent=`${value}%`;});
$<HTMLInputElement>('#head-turn').addEventListener('input',event=>{const value=Number((event.target as HTMLInputElement).value);if(viewer)viewer.state.headTurn=value;$('#head-turn-value').textContent=`${value>0?'+':''}${value}°`;});
$('#pause').addEventListener('click',()=>{if(viewer){viewer.pause(!viewer.state.paused);syncPause();}});
$('#blink-once').addEventListener('click',()=>{if(viewer?.state.paused)toast('Resume movement to play a blink.');else viewer?.blink();});
$('#reset').addEventListener('click',resetUI);
$('#idle').addEventListener('change',event=>{if(viewer)viewer.state.idle=(event.target as HTMLInputElement).checked;});
$('#hair').addEventListener('change',event=>{if(viewer)viewer.state.hairMotion=(event.target as HTMLInputElement).checked;});
$('#skin').addEventListener('change',event=>{viewer?.setScattering((event.target as HTMLInputElement).checked);if(viewer?.state.quality==='balanced')toast('Skin diffusion is available in High quality.');});
$('#quality').addEventListener('change',event=>viewer?.setQuality((event.target as HTMLSelectElement).value as 'high'|'balanced'));
$('#orbit').addEventListener('click',()=>{if(viewer){viewer.state.autoRotate=!viewer.state.autoRotate;$('#orbit').setAttribute('aria-pressed',String(viewer.state.autoRotate));}});
$('#fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('.studio').requestFullscreen();}catch{toast('Fullscreen is not available in this browser.');}});
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view as View)));
document.querySelectorAll<HTMLButtonElement>('[data-light]').forEach(button=>button.addEventListener('click',()=>{viewer?.setLighting(button.dataset.light as LightPreset);selectButtons('data-light',button.dataset.light!);}));
window.addEventListener('keydown',event=>{const target=event.target as HTMLElement;if(['INPUT','SELECT','BUTTON'].includes(target.tagName)||$<HTMLDialogElement>('#details-dialog').open)return;const views:Record<string,View>={'1':'portrait','2':'threeQuarter','3':'full'};if(views[event.key])setView(views[event.key]);if(event.code==='Space'){event.preventDefault();viewer?.pause(!viewer.state.paused);syncPause();}if(event.key.toLowerCase()==='r')resetUI();});
const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)');
reducedMotion.addEventListener('change',event=>{if(event.matches)viewer?.pause(true);syncPause();});
function errorState(message:string){sceneFailure=message;viewer?.cancelDiagnosticCapture('live-scene-unavailable');enableLiveControls(false);$<HTMLButtonElement>('#capture-diagnostics').disabled=false;$('#capture-diagnostics').textContent='Save readiness report';$('#diagnostic-status').textContent='Live 3D is unavailable. You can save the observed error and browser information locally.';$('#backend').textContent=viewer?'WEBGL 2 · NO LIVE SCENE':'WEBGL 2 UNAVAILABLE';$('#fps').textContent='—';$<HTMLElement>('#fallback-poster').hidden=false;$('#loading').classList.add('error');$('#loading').classList.remove('loaded');$('#loading-title').textContent='The study couldn’t load';$('#loading-subtitle').textContent=message;$<HTMLButtonElement>('#retry').hidden=false;$('#status-text').textContent='Scene unavailable';}
async function initialize(){
  const generation=++initializationGeneration;
  sceneFailure=null;enableLiveControls(false);$<HTMLButtonElement>('#capture-diagnostics').disabled=true;$('#capture-diagnostics').textContent='Capture 10 seconds';$('#diagnostic-status').textContent='Available after live 3D loads.';
  $<HTMLElement>('#fallback-poster').hidden=true;
  $('#loading').classList.remove('error');$('#loading-title').textContent='Bringing the study into focus';$('#loading-subtitle').textContent='Loading real 3D geometry & materials';$<HTMLButtonElement>('#retry').hidden=true;
  try {
    viewer?.dispose();viewer=null;releaseDiagnosticDownload();$<HTMLButtonElement>('#capture-diagnostics').disabled=true;viewer=new AvatarViewer($<HTMLCanvasElement>('#avatar-canvas'));
    viewer.onError=errorState;
    viewer.onStats=stats=>{if(sceneFailure)return;$('#fps').textContent=String(stats.fps);$('#backend').textContent=stats.backend.toUpperCase();};
    viewer.onDiagnosticComplete=report=>{const sample=report.sample as FrameCaptureResult;showDiagnosticReport(report,sample.status==='completed');};
    viewer.onDiagnosticProgress=remainingMs=>{const second=Math.ceil(remainingMs/1000);if(second!==diagnosticProgressSecond){diagnosticProgressSecond=second;$('#diagnostic-status').textContent=`Capturing locally: ${second} seconds remaining. Keep this tab visible. Settings changes are recorded.`;}};
    if(reducedMotion.matches)viewer.pause(true);
    // Exposed for reproducible checks and embedders. This is the real scene, not a test substitute.
    Object.assign(window,{avatarViewer:viewer});
    await viewer.load();
    if(generation!==initializationGeneration)return;
    enableLiveControls(true);$<HTMLButtonElement>('#capture-diagnostics').disabled=false;$('#diagnostic-status').textContent='Ready to observe the current settings. No performance budget is assumed.';
    $('#loading').classList.add('loaded');$('#character-name').textContent=viewer.config?.characterName??'The portrait study';$('#character-description').textContent=viewer.config?.description??'Made of geometry. Shaped by light.';
    syncPause();
  }catch(error){if(generation!==initializationGeneration)return;console.error(error);errorState(error instanceof Error?error.message:'An unexpected rendering error occurred.');}
}
$('#retry').addEventListener('click',()=>{void initialize();});
void initialize();
