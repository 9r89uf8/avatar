import { ArcRotateCamera } from '@babylonjs/core/Cameras/arcRotateCamera';
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color';
import { Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector';
import { DefaultRenderingPipeline } from '@babylonjs/core/PostProcesses/RenderPipeline/Pipelines/defaultRenderingPipeline';
import { DirectionalLight } from '@babylonjs/core/Lights/directionalLight';
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight';
import { Engine } from '@babylonjs/core/Engines/engine';
import { ImageProcessingConfiguration } from '@babylonjs/core/Materials/imageProcessingConfiguration';
import { ImportMeshAsync } from '@babylonjs/core/Loading/sceneLoader';
import { CreateGround } from '@babylonjs/core/Meshes/Builders/groundBuilder';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { SceneInstrumentation } from '@babylonjs/core/Instrumentation/sceneInstrumentation';
import { ShadowGenerator } from '@babylonjs/core/Lights/Shadows/shadowGenerator';
import { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import { VertexBuffer } from '@babylonjs/core/Buffers/buffer';
import type { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import type { AnimationGroup } from '@babylonjs/core/Animations/animationGroup';
import type { MorphTarget } from '@babylonjs/core/Morph/morphTarget';
import type { Observer } from '@babylonjs/core/Misc/observable';
import '@babylonjs/core/Rendering/prePassRendererSceneComponent';
import '@babylonjs/core/Rendering/subSurfaceSceneComponent';
import '@babylonjs/core/Lights/Shadows/shadowGeneratorSceneComponent';
import '@babylonjs/loaders/glTF';
import { createStudioEnvironment } from './environment';
import { blinkAt, clamp, damp, faceFrame, gazeAt } from './motion';
import { defaultState } from './types';
import { FrameCapture } from './diagnostics';
import { checkRuntimeSkinInfluences, inspectSkinInfluences, parseGlb } from './gltf-contract';
import type { RuntimeSkinInvariant, SkinInfluenceInventory } from './gltf-contract';
import type { DiagnosticValue } from './diagnostics';
import type { AvatarConfig, CameraPreset, LightPreset, ViewerState, ViewerStats, View } from './types';

interface RotationBinding { node:TransformNode; rest:Quaternion; }
const radial = (deg:number)=>deg*Math.PI/180;
export class AvatarViewer {
  readonly engine:Engine;
  readonly scene:Scene;
  readonly camera:ArcRotateCamera;
  readonly state:ViewerState={...defaultState};
  config:AvatarConfig|null=null;
  readonly stats:ViewerStats={fps:0,triangles:0,meshes:0,drawCalls:0,backend:'WebGL 2',materials:[],morphTargets:[],nodes:[],warnings:[],ready:false,paused:false,quality:'high',view:'portrait'};
  private pipeline:DefaultRenderingPipeline;
  private instrumentation:SceneInstrumentation;
  private key:DirectionalLight;
  private fill:DirectionalLight;
  private rim:DirectionalLight;
  private ambient:HemisphericLight;
  private shadow:ShadowGenerator;
  private head:RotationBinding|null=null;
  private hairs:RotationBinding[]=[];
  private eyes:RotationBinding[]=[];
  private gazeYaw=0;
  private gazePitch=0;
  private blinkTargets:MorphTarget[]=[];
  private smileTargets:MorphTarget[]=[];
  private breathTargets:MorphTarget[]=[];
  private skinMaterials:PBRMaterial[]=[];
  private clips:AnimationGroup[]=[];
  private elapsed=0;
  private manualBlinkStart:number|null=null;
  private smoothedHead=0;
  private smoothedSmile=0;
  private hairOffset=0;
  private hairVelocity=0;
  private lastHead=0;
  private avatarMeshes:AbstractMesh[]=[];
  private renderObserver:Observer<Scene>|null=null;
  private diagnosticObserver:Observer<Scene>|null=null;
  private readonly diagnosticSampler=new FrameCapture(10000);
  private disposed=false;
  private readonly loadAbort=new AbortController();
  private actualAssetSha256:string|null=null;
  private actualAssetBytes:number|null=null;
  private skinInfluenceInventory:SkinInfluenceInventory|null=null;
  private runtimeSkinInvariant:RuntimeSkinInvariant|null=null;
  private assetHashVerified:boolean|null=null;
  private readonly onVisibilityChange=()=>{if(document.hidden)this.diagnosticSampler.cancel('tab-hidden');};
  private resizeObserver:ResizeObserver;
  private cameraGoal:CameraPreset|null=null;
  private presets:Record<View,CameraPreset>={
    portrait:{target:[0,1.57,0],radius:0.92,alpha:Math.PI/2,beta:Math.PI/2},
    threeQuarter:{target:[0,1.40,0],radius:1.5,alpha:Math.PI/2-0.48,beta:Math.PI/2},
    full:{target:[0,0.87,0],radius:3.6,alpha:Math.PI/2,beta:1.45},
  };
  private readonly onCameraInteraction=()=>{this.cameraGoal=null;};
  private readyResolver:()=>void=()=>{};
  readonly ready:Promise<void>;
  onStats:((stats:ViewerStats)=>void)|null=null;
  onError:((message:string)=>void)|null=null;
  onDiagnosticComplete:((report:Record<string,unknown>)=>void)|null=null;
  onDiagnosticProgress:((remainingMs:number)=>void)|null=null;

  constructor(private canvas:HTMLCanvasElement) {
    this.ready=new Promise(resolve=>this.readyResolver=resolve);
    try{this.engine=new Engine(canvas,true,{preserveDrawingBuffer:true,stencil:true,antialias:true,disableWebGL2Support:false,powerPreference:'high-performance'},true);}
    catch(error){throw new Error('WebGL 2 is unavailable on this device or browser. The image shown is a still render, not live 3D.',{cause:error});}
    if(this.engine.webGLVersion<2){this.engine.dispose();throw new Error('WebGL 2 is unavailable on this device or browser. The image shown is a still render, not live 3D.');}
    this.engine.setHardwareScalingLevel(1/Math.min(window.devicePixelRatio,1.75));
    this.scene=new Scene(this.engine);
    this.scene.useRightHandedSystem=true;
    this.scene.clearColor=new Color4(0,0,0,0);
    this.scene.environmentIntensity=0.65;
    this.scene.imageProcessingConfiguration.toneMappingEnabled=true;
    this.scene.imageProcessingConfiguration.toneMappingType=ImageProcessingConfiguration.TONEMAPPING_ACES;
    this.scene.imageProcessingConfiguration.exposure=1.0;
    this.scene.imageProcessingConfiguration.contrast=1.0;
    this.camera=new ArcRotateCamera('Inspection camera',Math.PI/2,1.5,0.92,new Vector3(0,1.57,0),this.scene);
    this.camera.minZ=0.02;this.camera.maxZ=100;
    this.camera.fov=radial(31);
    this.camera.lowerRadiusLimit=0.32;this.camera.upperRadiusLimit=6;
    this.camera.lowerBetaLimit=0.15;this.camera.upperBetaLimit=Math.PI-0.15;
    this.camera.wheelDeltaPercentage=0.018;
    this.camera.pinchDeltaPercentage=0.0015;
    this.camera.panningSensibility=950;
    this.camera.angularSensibilityX=1100;this.camera.angularSensibilityY=1100;
    this.camera.inertia=0.78;
    this.camera.attachControl(canvas,true);
    canvas.addEventListener('pointerdown',this.onCameraInteraction);
    canvas.addEventListener('wheel',this.onCameraInteraction,{passive:true});
    this.key=new DirectionalLight('Large softbox / key',new Vector3(0.45,-0.35,-0.8),this.scene);
    this.key.position.set(-2,3,3);this.key.diffuse=new Color3(1,0.94,0.87);this.key.intensity=2.35;
    this.fill=new DirectionalLight('Cool bounce / fill',new Vector3(-0.8,-0.15,-0.45),this.scene);
    this.fill.diffuse=new Color3(0.85,0.92,1);this.fill.intensity=0.62;
    this.rim=new DirectionalLight('Hair separation / rim',new Vector3(-0.25,-0.55,0.78),this.scene);
    this.rim.diffuse=new Color3(0.87,0.92,1);this.rim.intensity=1.75;
    this.ambient=new HemisphericLight('Subtle floor bounce',new Vector3(0,1,0),this.scene);
    this.ambient.intensity=0.13;this.ambient.groundColor=new Color3(0.18,0.16,0.14);
    this.shadow=new ShadowGenerator(2048,this.key);
    this.shadow.usePercentageCloserFiltering=true;this.shadow.filteringQuality=ShadowGenerator.QUALITY_HIGH;
    this.shadow.bias=0.0003;this.shadow.normalBias=0.002;
    this.key.shadowMinZ=0.1;this.key.shadowMaxZ=10;
    const ground=CreateGround('Studio floor',{width:200,height:200},this.scene);
    const floor=new PBRMaterial('Studio floor material',this.scene);floor.albedoColor=new Color3(0.08,0.083,0.078);floor.roughness=0.92;floor.metallic=0;
    ground.material=floor;ground.receiveShadows=true;ground.position.y=-0.012;ground.isPickable=false;
    ground.visibility=0; // The UI's continuous studio backdrop is the portrait background.
    this.pipeline=new DefaultRenderingPipeline('Portrait resolve',true,this.scene,[this.camera]);
    this.pipeline.samples=4;this.pipeline.fxaaEnabled=true;this.pipeline.bloomEnabled=false;
    this.pipeline.imageProcessingEnabled=true;
    this.pipeline.sharpenEnabled=true;this.pipeline.sharpen.edgeAmount=0.12;this.pipeline.sharpen.colorAmount=1;
    this.instrumentation=new SceneInstrumentation(this.scene);
    this.renderObserver=this.scene.onBeforeRenderObservable.add(()=>this.update());
    this.diagnosticObserver=this.scene.onAfterRenderObservable.add(()=>{
      if(!this.diagnosticSampler.active)return;
      this.diagnosticSampler.record(performance.now(),this.instrumentation.drawCallsCounter.current,this.getDiagnosticState());
      if(this.diagnosticSampler.active)this.onDiagnosticProgress?.(this.diagnosticSampler.remainingMs);
    });
    document.addEventListener('visibilitychange',this.onVisibilityChange);
    this.resizeObserver=new ResizeObserver(()=>this.engine.resize());this.resizeObserver.observe(canvas);
    this.engine.onContextLostObservable.add(()=>{this.diagnosticSampler.cancel('graphics-context-lost');this.onError?.('The graphics context was interrupted. The image shown is a still render. Retry to restore live 3D.');});
    this.engine.runRenderLoop(()=>{if(!document.hidden)this.scene.render();});
  }

  async load(configUrl='/assets/avatar.web.json'):Promise<void> {
    const response=await fetch(configUrl,{cache:'no-cache',signal:this.loadAbort.signal});
    if(!response.ok) throw new Error(`The character settings are not available (${response.status}).`);
    const config=await response.json() as AvatarConfig;
    if(config.schemaVersion!==1 || typeof config.modelUrl!=='string' || !Array.isArray(config.skinMaterials)) throw new Error('Invalid character configuration. Expected schemaVersion 1, modelUrl and exact skinMaterials.');
    this.config=config;
    await createStudioEnvironment(this.scene);
    if(this.disposed)throw new Error('Viewer was disposed during loading.');
    const modelResponse=await fetch(config.modelUrl,{cache:'no-cache',signal:this.loadAbort.signal});
    if(!modelResponse.ok)throw new Error(`The 3D character is not available (${modelResponse.status}).`);
    const modelBytes=await modelResponse.arrayBuffer();
    this.actualAssetBytes=modelBytes.byteLength;
    const expectedHash=config.modelSha256??config.glbSha256;
    if(globalThis.crypto?.subtle){
      const digest=await crypto.subtle.digest('SHA-256',modelBytes);
      const actualHash=Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');
      this.actualAssetSha256=actualHash;
      this.assetHashVerified=expectedHash?actualHash===expectedHash.toLowerCase():null;
      if(expectedHash && !this.assetHashVerified)throw new Error('The character and material settings do not match. Please reload after the export completes.');
    }
    const parsedGlb=parseGlb(new Uint8Array(modelBytes));
    this.skinInfluenceInventory=inspectSkinInfluences(parsedGlb.gltf,parsedGlb.binary);
    if(this.skinInfluenceInventory.issues.length)throw new Error(`The character exceeds or violates this viewer's skinning contract: ${this.skinInfluenceInventory.issues.join(' ')}`);
    if(this.disposed)throw new Error('Viewer was disposed during loading.');
    const result=await ImportMeshAsync(new Uint8Array(modelBytes),this.scene,{pluginExtension:'.glb',pluginOptions:{gltf:{animationStartMode:0}},name:'avatar.glb',rootUrl:new URL('.',new URL(config.modelUrl,location.href)).href});
    this.avatarMeshes=result.meshes.filter(mesh=>mesh.getTotalVertices()>0);
    this.runtimeSkinInvariant=checkRuntimeSkinInfluences(this.skinInfluenceInventory,this.avatarMeshes.map(mesh=>({name:mesh.name,numBoneInfluencers:mesh.numBoneInfluencers,pointers:this.getPrimitivePointers(mesh),hasExtraJointBuffer:mesh.isVerticesDataPresent(VertexBuffer.MatricesIndicesExtraKind),hasExtraWeightBuffer:mesh.isVerticesDataPresent(VertexBuffer.MatricesWeightsExtraKind)})));
    if(this.runtimeSkinInvariant.issues.length)throw new Error(`Eight-weight skinning did not load correctly: ${this.runtimeSkinInvariant.issues.join(' ')}`);
    this.clips=result.animationGroups;this.clips.forEach(clip=>clip.stop());
    this.scene.meshes.forEach(mesh=>{if(mesh.material instanceof PBRMaterial){mesh.material.maxSimultaneousLights=4;mesh.material.useRadianceOverAlpha=false;mesh.material.useSpecularOverAlpha=false;}});
    const exact=new Map(this.scene.materials.map(material=>[material.name,material]));
    config.skinMaterials.forEach(name=>{
      const material=exact.get(name);
      if(!(material instanceof PBRMaterial)){this.stats.warnings.push(`Skin material missing or not PBR: ${name}`);return;}
      material.metallic=0;
      material.roughness=config.skin?.roughness??material.roughness??0.48;
      material.specularIntensity=config.skin?.specularIntensity??0.55;
      material.subSurface.indexOfRefraction=1.4;
      material.subSurface.isRefractionEnabled=false;
      material.subSurface.isTranslucencyEnabled=false;
      material.subSurface.minimumThickness=0;
      material.subSurface.maximumThickness=(config.skin?.thicknessMillimeters??2)/1000/(config.metersPerUnit??1);
      material.subSurface.tintColor=new Color3(0.92,0.53,0.4);
      material.subSurface.scatteringDiffusionProfile=Color3.FromArray(config.skin?.diffusion??[1,0.32,0.16]);
      this.skinMaterials.push(material);
    });
    const groomMaterial=exact.get('GroomDarkBrownCards');
    if(groomMaterial instanceof PBRMaterial){
      groomMaterial.transparencyMode=PBRMaterial.PBRMATERIAL_ALPHATEST;
      groomMaterial.useAlphaFromAlbedoTexture=true;
      groomMaterial.alphaCutOff=config.hair?.alphaCutOff??0.32;
      groomMaterial.enableSpecularAntiAliasing=true;
      if(groomMaterial.albedoTexture)groomMaterial.albedoTexture.hasAlpha=true;
      // Keep authored roughness, specular strength, anisotropy and double-sided normals.
      // Alpha test writes depth coherently; FXAA/MSAA resolve the silhouette, no sorted blending.
    }
    const ss=this.scene.enableSubSurfaceForPrePass();if(ss)ss.metersPerUnit=config.metersPerUnit??1;
    this.setScattering(this.state.scattering);
    const allNodes=[...result.transformNodes,...result.meshes];
    const bind=(name:string|undefined):RotationBinding|null=>{
      if(!name)return null;const node=allNodes.find(n=>n.name===name)??this.scene.getTransformNodeByName(name);
      if(!node){this.stats.warnings.push(`Control node missing: ${name}`);return null;}
      const rest=node.rotationQuaternion?.clone()??Quaternion.FromEulerVector(node.rotation);
      node.rotationQuaternion=rest.clone();return{node,rest};
    };
    this.head=bind(config.headNode);
    this.eyes=(config.eyeNodes??['eye.L','eye.R']).map(bind).filter((binding):binding is RotationBinding=>binding!==null);
    this.hairs=(config.hairNodes??[]).map(bind).filter((binding):binding is RotationBinding=>binding!==null);
    const targets=new Map<string,MorphTarget[]>();
    result.meshes.forEach(mesh=>{const manager=mesh.morphTargetManager;if(manager)for(let i=0;i<manager.numTargets;i++){const target=manager.getTarget(i);targets.set(target.name,[...(targets.get(target.name)??[]),target]);}});
    const findTargets=(names:string[]=[])=>names.flatMap(name=>{const target=targets.get(name);if(!target)this.stats.warnings.push(`Morph target missing: ${name}`);return target??[];});
    this.blinkTargets=findTargets(config.morphTargets?.blink);
    this.smileTargets=findTargets(config.morphTargets?.smile);
    this.breathTargets=findTargets(config.morphTargets?.breath);
    const nonShadowMaterials=new Set(config.nonShadowMaterials??['CorneaOptical']);
    this.avatarMeshes.forEach(mesh=>{
      // A transmissive corneal shell must not occlude the opaque iris beneath it.
      const opticalShell=nonShadowMaterials.has(mesh.material?.name??'');
      if(!opticalShell)this.shadow.addShadowCaster(mesh);
      mesh.receiveShadows=!opticalShell;mesh.alwaysSelectAsActiveMesh=true;
    });
    this.scene.render();
    const bounds=this.scene.getWorldExtends(mesh=>this.avatarMeshes.includes(mesh));
    const f=faceFrame(bounds.min.asArray() as [number,number,number],bounds.max.asArray() as [number,number,number]);
    if(!Number.isFinite(f.height)||f.height<0.1)throw new Error('The character has invalid dimensions.');
    this.presets={
      portrait:{target:[f.centerX,f.headY,f.centerZ],radius:f.height*0.53,alpha:Math.PI/2,beta:1.535},
      threeQuarter:{target:[f.centerX,bounds.min.y+f.height*0.83,f.centerZ],radius:f.height*0.83,alpha:Math.PI/2-0.52,beta:1.49},
      full:{target:[f.centerX,bounds.min.y+f.height*0.51,f.centerZ],radius:f.height*2.06,alpha:Math.PI/2,beta:1.48},
      ...config.cameras,
    };
    this.camera.lowerRadiusLimit=f.height*0.18;this.camera.upperRadiusLimit=f.height*4.5;
    this.setView('portrait',false);
    this.stats.triangles=this.avatarMeshes.reduce((total,mesh)=>total+mesh.getTotalIndices()/3,0);
    this.stats.meshes=this.avatarMeshes.length;
    this.stats.materials=result.meshes.map(mesh=>mesh.material?.name).filter((v):v is string=>Boolean(v)).filter((v,i,a)=>a.indexOf(v)===i);
    this.stats.morphTargets=[...targets.keys()];this.stats.nodes=allNodes.map(node=>node.name);
    await this.scene.whenReadyAsync();
    this.stats.ready=true;
    this.readyResolver();this.onStats?.(this.stats);
  }

  setView(view:View,animate=true):void {
    this.state.view=view;this.stats.view=view;
    const preset=this.presets[view];
    this.camera.inertialAlphaOffset=0;this.camera.inertialBetaOffset=0;this.camera.inertialRadiusOffset=0;
    if(animate)this.cameraGoal={...preset,target:[...preset.target]};
    else{this.cameraGoal=null;this.camera.alpha=preset.alpha;this.camera.beta=preset.beta;this.camera.radius=preset.radius;this.camera.target.copyFromFloats(...preset.target);}
  }
  setScattering(enabled:boolean):void {
    this.state.scattering=enabled;
    this.skinMaterials.forEach(material=>{material.subSurface.isScatteringEnabled=enabled && this.state.quality==='high';});
  }
  setQuality(quality:'high'|'balanced'):void {
    this.state.quality=quality;this.stats.quality=quality;
    this.engine.setHardwareScalingLevel(1/Math.min(window.devicePixelRatio,quality==='high'?1.75:1.0));
    this.pipeline.samples=quality==='high'?4:1;this.shadow.filteringQuality=quality==='high'?ShadowGenerator.QUALITY_HIGH:ShadowGenerator.QUALITY_LOW;
    this.setScattering(this.state.scattering);this.engine.resize();
  }
  setLighting(light:LightPreset):void {
    this.state.light=light;
    const presets={studio:[2.35,0.62,1.75,0.65],daylight:[1.9,0.95,0.9,0.9],rim:[0.95,0.2,3.8,0.34]} as const;
    const [key,fill,rim,env]=presets[light];this.key.intensity=key;this.fill.intensity=fill;this.rim.intensity=rim;this.scene.environmentIntensity=env;
    this.key.diffuse=light==='daylight'?new Color3(0.95,0.97,1):new Color3(1,0.94,0.87);
  }
  blink():void {this.manualBlinkStart=this.elapsed;}
  reset():void {
    this.diagnosticSampler.reset();
    Object.assign(this.state,{...defaultState,paused:window.matchMedia('(prefers-reduced-motion: reduce)').matches});
    this.elapsed=0;this.gazeYaw=0;this.gazePitch=0;this.smoothedHead=0;this.smoothedSmile=0;this.hairOffset=0;this.hairVelocity=0;this.lastHead=0;this.manualBlinkStart=null;
    this.blinkTargets.forEach(t=>t.influence=0);this.smileTargets.forEach(t=>t.influence=0);this.breathTargets.forEach(t=>t.influence=0);
    if(this.head)this.head.node.rotationQuaternion?.copyFrom(this.head.rest);
    this.hairs.forEach(binding=>binding.node.rotationQuaternion?.copyFrom(binding.rest));
    this.eyes.forEach(binding=>binding.node.rotationQuaternion?.copyFrom(binding.rest));
    this.setLighting('studio');this.setQuality('high');this.setView('portrait');
  }
  pause(paused:boolean):void {this.state.paused=paused;this.stats.paused=paused;}
  getInventory():ViewerStats {return {...this.stats,paused:this.state.paused};}
  private getPrimitivePointers(mesh:AbstractMesh):string[]{
    // The pinned glTF loader writes its exact JSON pointers here (GLTFLoader.AddPointerMetadata).
    const pointers:unknown=mesh._internalMetadata?.gltf?.pointers;
    return Array.isArray(pointers)?pointers.filter((pointer):pointer is string=>typeof pointer==='string'):[];
  }
  get diagnosticActive():boolean{return this.diagnosticSampler.active;}
  private getDiagnosticState():DiagnosticValue {
    const rect=this.canvas.getBoundingClientRect();
    return{
      requested:{...this.state},
      reducedMotionPreference:window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      pageVisible:!document.hidden,
      effective:{
        animationAdvancing:this.stats.ready&&!this.state.paused&&!document.hidden,
        microgazeEnabled:this.state.idle,
        microgazeAdvancing:this.state.idle&&!this.state.paused&&this.eyes.length>0&&!document.hidden,
        microgazeControlledBy:'idle',microgazeYawLimitDegrees:2,microgazePitchLimitDegrees:1,
        eyeBindings:this.eyes.length,
        hairEnabled:this.state.hairMotion,hairAdvancing:this.state.hairMotion&&!this.state.paused&&this.hairs.length>0&&!document.hidden,hairBindings:this.hairs.length,
        skinDiffusionEnabled:this.skinMaterials.some(material=>material.subSurface.isScatteringEnabled),
        msaaSamples:this.pipeline.samples,fxaaEnabled:this.pipeline.fxaaEnabled,
      },
      viewport:{cssWidth:rect.width,cssHeight:rect.height,renderWidth:this.engine.getRenderWidth(),renderHeight:this.engine.getRenderHeight(),devicePixelRatio:window.devicePixelRatio,hardwareScalingLevel:this.engine.getHardwareScalingLevel()},
    };
  }
  getDiagnosticSnapshot():Record<string,unknown> {
    const caps=this.engine.getCaps(),gl=this.engine.getGlInfo();
    const deviceMemory=(navigator as Navigator & {deviceMemory?:number}).deviceMemory;
    return{
      engine:{name:'Babylon.js',version:Engine.Version,backend:`WebGL ${this.engine.webGLVersion}`,renderer:gl.renderer,vendor:gl.vendor,versionString:gl.version,rendererDisclosure:'Browser-reported information may be masked, virtualized, or software-rendered.'},
      browser:{userAgent:navigator.userAgent,logicalProcessors:navigator.hardwareConcurrency??null,reportedMemoryGiB:deviceMemory??null,secureContext:window.isSecureContext},
      capabilities:{
        maxTextureSize:caps.maxTextureSize,maxCubeTextureSize:caps.maxCubemapTextureSize,maxRenderTextureSize:caps.maxRenderTextureSize,maxTextureUnits:caps.maxTexturesImageUnits,maxVertexAttributes:caps.maxVertexAttribs,maxMSAASamples:caps.maxMSAASamples,maxDrawBuffers:caps.maxDrawBuffers??null,maxAnisotropy:caps.maxAnisotropy,
        floatTextures:caps.textureFloat,floatTextureLinearFiltering:caps.textureFloatLinearFiltering,floatRenderTargets:caps.textureFloatRender,halfFloatRenderTargets:caps.textureHalfFloatRender,depthTextures:caps.depthTextureExtension,drawBuffers:caps.drawBuffersExtension,instancing:caps.instancedArrays,textureLOD:caps.textureLOD,highPrecisionShaders:caps.highPrecisionShaderSupported,
        gpuTimerQueryAvailable:Boolean(caps.timerQuery),gpuTimingsMeasured:false,
        textureCompression:{astc:Boolean(caps.astc),bptc:Boolean(caps.bptc),etc2:Boolean(caps.etc2),s3tc:Boolean(caps.s3tc),pvrtc:Boolean(caps.pvrtc)},
      },
      asset:{modelUrl:this.config?.modelUrl??null,actualSha256:this.actualAssetSha256,expectedSha256:this.config?.modelSha256??this.config?.glbSha256??null,hashMatchesSidecar:this.assetHashVerified,hashObservation:this.actualAssetSha256?'Computed from the loaded GLB bytes.':'Web Crypto SHA-256 was unavailable; no actual hash is claimed.',bytes:this.actualAssetBytes,triangles:this.stats.triangles,geometryMeshCount:this.avatarMeshes.length,totalSceneMeshCount:this.scene.meshes.length,skeletonCount:this.scene.skeletons.length,skeletons:this.scene.skeletons.map(skeleton=>({name:skeleton.name,bones:skeleton.bones.length})),meshInfluences:this.avatarMeshes.map(mesh=>({name:mesh.name,numBoneInfluencers:mesh.numBoneInfluencers,sourcePointers:this.getPrimitivePointers(mesh),extraJointBufferPresent:mesh.isVerticesDataPresent(VertexBuffer.MatricesIndicesExtraKind),extraWeightBufferPresent:mesh.isVerticesDataPresent(VertexBuffer.MatricesWeightsExtraKind),useBones:mesh.useBones,computeBonesUsingShaders:mesh.computeBonesUsingShaders,skeleton:mesh.skeleton?.name??null,vertices:mesh.getTotalVertices(),triangles:mesh.getTotalIndices()/3})),materials:[...this.stats.materials],sourcePrimitiveInfluences:this.skinInfluenceInventory,runtimeSkinInvariant:this.runtimeSkinInvariant},
      state:this.getDiagnosticState(),
      camera:{alpha:this.camera.alpha,beta:this.camera.beta,radius:this.camera.radius,target:this.camera.target.asArray(),verticalFovRadians:this.camera.fov},
      bindingWarnings:[...this.stats.warnings],
    };
  }
  captureDiagnostics():void {
    if(this.disposed||!this.stats.ready)throw new Error('Wait for live 3D to load before measuring frame times.');
    if(document.hidden)throw new Error('Keep this tab visible while capturing diagnostics.');
    const initial=this.getDiagnosticSnapshot(),startedAt=new Date().toISOString();
    this.diagnosticSampler.start(this.getDiagnosticState(),sample=>{
      this.onDiagnosticComplete?.({schemaVersion:1,reportType:'avatar-local-render-diagnostics',createdAt:new Date().toISOString(),startedAt,privacy:'Created in this browser only. No telemetry was sent. The report is downloaded locally only at your request.',initial,final:this.getDiagnosticSnapshot(),sample,limitations:['No performance budget or pass/fail threshold has been assumed.','This sample does not establish photorealism, identity fidelity, or target-device certification.','Frame intervals are browser render-callback observations, not isolated GPU timing.','The open details panel and diagnostic instrumentation may affect observed timings.','Paused animation still renders frames; motion and reduced-motion settings are recorded explicitly.']});
    });
    this.onDiagnosticProgress?.(this.diagnosticSampler.remainingMs);
  }
  cancelDiagnosticCapture(reason='user-cancelled'):void {this.diagnosticSampler.cancel(reason);}
  private update():void {
    const dt=clamp(this.engine.getDeltaTime()/1000,0,0.05);
    if(this.cameraGoal){
      const p=this.cameraGoal;const blend=1-Math.exp(-8*dt);
      this.camera.alpha=damp(this.camera.alpha,p.alpha,8,dt);this.camera.beta=damp(this.camera.beta,p.beta,8,dt);this.camera.radius=damp(this.camera.radius,p.radius,8,dt);
      Vector3.LerpToRef(this.camera.target,Vector3.FromArray(p.target),blend,this.camera.target);
      if(Math.abs(this.camera.radius-p.radius)<0.0001 && Math.abs(this.camera.alpha-p.alpha)<0.0001)this.cameraGoal=null;
    }
    if(this.stats.ready && !this.state.paused){
      this.elapsed+=dt;
      const idle=this.state.idle;
      this.smoothedHead=damp(this.smoothedHead,radial(this.state.headTurn)+(idle?0.015*Math.sin(this.elapsed*0.57):0),6,dt);
      this.smoothedSmile=damp(this.smoothedSmile,this.state.smile,8,dt);
      const gaze=idle?gazeAt(this.elapsed):{yaw:0,pitch:0};
      this.gazeYaw=damp(this.gazeYaw,radial(gaze.yaw),12,dt);this.gazePitch=damp(this.gazePitch,radial(gaze.pitch),12,dt);
      // MPFB eye bone local Y points forward. Z is gaze yaw, X is pitch; Y would twist the iris.
      this.eyes.forEach(binding=>{binding.node.rotationQuaternion=binding.rest.multiply(Quaternion.FromEulerAngles(this.gazePitch,0,this.gazeYaw));});
      if(this.head){const offset=Quaternion.FromEulerAngles(idle?Math.sin(this.elapsed*0.7)*0.006:0,this.smoothedHead,idle?Math.sin(this.elapsed*0.39)*0.004:0);this.head.node.rotationQuaternion=this.head.rest.multiply(offset);}
      let blink=this.state.blink?blinkAt(this.elapsed):0;
      if(this.manualBlinkStart!==null){const t=this.elapsed-this.manualBlinkStart;if(t<0.285)blink=blinkAt(t-0.42);else this.manualBlinkStart=null;}
      this.blinkTargets.forEach(target=>target.influence=clamp(blink,0,1));
      this.smileTargets.forEach(target=>target.influence=this.smoothedSmile);
      this.breathTargets.forEach(target=>target.influence=idle?0.2+0.18*Math.sin(this.elapsed*1.32):0);
      const headVelocity=(this.smoothedHead-this.lastHead)/Math.max(dt,0.001);this.lastHead=this.smoothedHead;
      const springTarget=this.state.hairMotion?clamp(-headVelocity*0.055,-0.045,0.045):0;
      // Semi-implicit damped spring, substepped for stability during slow frames.
      const steps=Math.max(1,Math.ceil(dt/(1/120)));const h=dt/steps;
      for(let i=0;i<steps;i++){this.hairVelocity+=(50*(springTarget-this.hairOffset)-11*this.hairVelocity)*h;this.hairOffset+=this.hairVelocity*h;}
      this.hairOffset=clamp(this.hairOffset,-0.065,0.065);
      this.hairs.forEach(binding=>{
        const strength=binding.node.name.includes('Root')?0.22:binding.node.name.includes('Mid')?0.66:1;
        const side=binding.node.name.endsWith('.R')?-1:1;
        binding.node.rotationQuaternion=binding.rest.multiply(Quaternion.FromEulerAngles(this.hairOffset*strength*0.28,this.hairOffset*strength*0.35,this.hairOffset*strength*side));
      });
      if(this.state.autoRotate&&!this.cameraGoal)this.camera.alpha+=dt*0.13;
    }
    const frame=this.engine.frameId;
    if(frame%30===0){this.stats.fps=Math.round(this.engine.getFps());this.stats.drawCalls=this.instrumentation.drawCallsCounter.current;this.stats.paused=this.state.paused;this.onStats?.(this.stats);}
  }
  dispose():void {
    if(this.disposed)return;
    this.diagnosticSampler.dispose();this.disposed=true;this.loadAbort.abort();
    document.removeEventListener('visibilitychange',this.onVisibilityChange);
    if(this.diagnosticObserver)this.scene.onAfterRenderObservable.remove(this.diagnosticObserver);
    this.onDiagnosticComplete=null;this.onDiagnosticProgress=null;
    this.canvas.removeEventListener('pointerdown',this.onCameraInteraction);this.canvas.removeEventListener('wheel',this.onCameraInteraction);
    this.resizeObserver.disconnect();if(this.renderObserver)this.scene.onBeforeRenderObservable.remove(this.renderObserver);
    this.clips.forEach(clip=>clip.dispose());this.instrumentation.dispose();this.scene.dispose();this.engine.dispose();
  }
}
