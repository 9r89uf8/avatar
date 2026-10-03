import { Color3 } from '@babylonjs/core/Maths/math.color';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Constants } from '@babylonjs/core/Engines/constants';
import { RawCubeTexture } from '@babylonjs/core/Materials/Textures/rawCubeTexture';
import { Texture } from '@babylonjs/core/Materials/Textures/texture';
import { Scene } from '@babylonjs/core/scene';
import { CubeMapToSphericalPolynomialTools } from '@babylonjs/core/Misc/HighDynamicRange/cubemapToSphericalPolynomial';
import { HDRFiltering } from '@babylonjs/core/Materials/Textures/Filtering/hdrFiltering';

/** A project-owned linear HDR studio, generated locally. No network HDR dependencies. */
export async function createStudioEnvironment(scene:Scene):Promise<RawCubeTexture> {
  const size=64;
  const faces:Float32Array[]=[];
  const key=new Vector3(-0.65,0.60,0.55).normalize();
  const fill=new Vector3(0.85,0.25,0.45).normalize();
  const edge=new Vector3(0.2,0.65,-0.72).normalize();
  for(let f=0;f<6;f++) {
    const data=new Float32Array(size*size*3);
    for(let y=0;y<size;y++) for(let x=0;x<size;x++) {
      const u=(2*(x+0.5)/size)-1, v=(2*(y+0.5)/size)-1;
      const d=[new Vector3(1,-v,-u),new Vector3(-1,-v,u),new Vector3(u,1,v),new Vector3(u,-1,-v),new Vector3(u,-v,1),new Vector3(-u,-v,-1)][f].normalize();
      const ambient=0.12+0.15*Math.max(d.y,0);
      const k=3.5*Math.exp((Vector3.Dot(d,key)-1)*18);
      const b=1.1*Math.exp((Vector3.Dot(d,fill)-1)*10);
      const r=2.8*Math.exp((Vector3.Dot(d,edge)-1)*35);
      const color=new Color3(ambient+k*1.0+b*0.83+r*0.88,ambient+k*0.92+b*0.91+r*0.93,ambient+k*0.82+b+r);
      const i=(y*size+x)*3; data[i]=color.r;data[i+1]=color.g;data[i+2]=color.b;
    }
    faces.push(data);
  }
  const environment=new RawCubeTexture(scene,faces,size,Constants.TEXTUREFORMAT_RGB,Constants.TEXTURETYPE_FLOAT,true,false,Texture.TRILINEAR_SAMPLINGMODE);
  environment.name='Atelier / linear HDR studio';
  environment.gammaSpace=false;
  environment.sphericalPolynomial=CubeMapToSphericalPolynomialTools.ConvertCubeMapToSphericalPolynomial({size,format:Constants.TEXTUREFORMAT_RGB,type:Constants.TEXTURETYPE_FLOAT,gammaSpace:false,right:faces[0],left:faces[1],up:faces[2],down:faces[3],front:faces[4],back:faces[5]});
  scene.environmentTexture=environment;
  try { await new HDRFiltering(scene.getEngine(),{quality:64}).prefilter(environment); }
  catch(error) { console.warn('Studio reflection prefilter unavailable; using generated mip levels.',error); }
  return environment;
}
