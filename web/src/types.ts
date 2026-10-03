export type View = 'portrait' | 'threeQuarter' | 'full';
export type LightPreset = 'studio' | 'daylight' | 'rim';
export interface CameraPreset { target: [number, number, number]; radius: number; alpha: number; beta: number; }
export interface AvatarConfig {
  schemaVersion: 1;
  modelUrl: string;
  modelSha256?: string;
  glbSha256?: string;
  characterName?: string;
  description?: string;
  metersPerUnit?: number;
  skinMaterials: string[];
  eyeMaterials?: string[];
  hairMaterials?: string[];
  nonShadowMaterials?: string[];
  headNode?: string;
  neckNode?: string;
  eyeNodes?: string[];
  hairNodes?: string[];
  morphTargets?: { blink?: string[]; smile?: string[]; breath?: string[] };
  cameras?: Partial<Record<View, CameraPreset>>;
  hair?: { alphaCutOff?: number; };
  skin?: { roughness?: number; specularIntensity?: number; diffusion?: [number,number,number]; thicknessMillimeters?: number; };
}
export interface ViewerStats { fps:number; triangles:number; meshes:number; drawCalls:number; backend:string; materials:string[]; morphTargets:string[]; nodes:string[]; warnings:string[]; ready:boolean; paused:boolean; quality:string; view:View; }
export interface ViewerState { paused:boolean; idle:boolean; blink:boolean; smile:number; headTurn:number; autoRotate:boolean; scattering:boolean; hairMotion:boolean; light:LightPreset; quality:'high'|'balanced'; view:View; }
export const defaultState: ViewerState = {paused:false,idle:true,blink:true,smile:0,headTurn:0,autoRotate:false,scattering:true,hairMotion:true,light:'studio',quality:'high',view:'portrait'};
