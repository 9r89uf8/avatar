interface Accessor {bufferView?:number;byteOffset?:number;componentType:number;count:number;type:string;normalized?:boolean;sparse?:{count:number;indices:{bufferView:number;byteOffset?:number;componentType:number};values:{bufferView:number;byteOffset?:number}};}
interface BufferView {buffer:number;byteOffset?:number;byteLength:number;byteStride?:number;}
export interface GltfDocument {asset?:{version?:string};buffers?:{uri?:string;byteLength:number}[];bufferViews?:BufferView[];accessors?:Accessor[];meshes?:{name?:string;primitives:{attributes:Record<string,number>}[]}[];}
export interface SkinInfluenceInventory {issues:string[];primitives:{mesh:string;meshIndex:number;primitiveIndex:number;weightSets:string[];vertices:number;maxNonzeroWeights:number|null;meanNonzeroWeights:number|null;unreadableReason:string|null}[];}
export function parseGlb(bytes:Uint8Array):{gltf:GltfDocument;binary:Uint8Array}{
  if(bytes.byteLength<20)throw new Error('Invalid GLB header.');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  if(view.getUint32(0,true)!==0x46546c67||view.getUint32(4,true)!==2)throw new Error('Expected a glTF 2.0 binary asset.');
  if(view.getUint32(8,true)!==bytes.byteLength)throw new Error('GLB length does not match its header.');
  let gltf:GltfDocument|null=null;let binary:Uint8Array=new Uint8Array();
  for(let offset=12;offset+8<=bytes.byteLength;){
    const length=view.getUint32(offset,true),type=view.getUint32(offset+4,true);offset+=8;
    if(offset+length>bytes.byteLength)throw new Error('Invalid GLB chunk length.');
    const chunk=bytes.subarray(offset,offset+length);
    if(type===0x4e4f534a)gltf=JSON.parse(new TextDecoder().decode(chunk)) as GltfDocument;
    if(type===0x004e4942)binary=chunk;
    offset+=length;
  }
  if(!gltf)throw new Error('GLB has no JSON document.');
  return{gltf,binary};
}
const componentBytes:Record<number,number>={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};
function readComponent(view:DataView,offset:number,type:number):number{
  switch(type){case 5120:return view.getInt8(offset);case 5121:return view.getUint8(offset);case 5122:return view.getInt16(offset,true);case 5123:return view.getUint16(offset,true);case 5125:return view.getUint32(offset,true);case 5126:return view.getFloat32(offset,true);default:throw new Error(`Unsupported accessor component type ${type}`);}
}
function readWeights(gltf:GltfDocument,binary:Uint8Array,index:number):Float64Array{
  const accessor=gltf.accessors?.[index];if(!accessor||accessor.type!=='VEC4')throw new Error(`Weight accessor ${index} must be VEC4.`);
  const size=componentBytes[accessor.componentType];if(!size)throw new Error('Unsupported weight component type.');
  const values=new Float64Array(accessor.count*4),view=new DataView(binary.buffer,binary.byteOffset,binary.byteLength);
  const getView=(index:number)=>{const bv=gltf.bufferViews?.[index];if(!bv||bv.buffer!==0||gltf.buffers?.[0]?.uri)throw new Error('Weight buffer is not embedded in this GLB.');return bv;};
  if(accessor.bufferView!==undefined){const bv=getView(accessor.bufferView),base=(bv.byteOffset??0)+(accessor.byteOffset??0),stride=bv.byteStride??4*size;for(let vertex=0;vertex<accessor.count;vertex++)for(let channel=0;channel<4;channel++)values[vertex*4+channel]=readComponent(view,base+vertex*stride+channel*size,accessor.componentType);}
  if(accessor.sparse){const sparse=accessor.sparse,indices=getView(sparse.indices.bufferView),replacement=getView(sparse.values.bufferView),indexSize=componentBytes[sparse.indices.componentType];if(!indexSize)throw new Error('Unsupported sparse index type.');for(let i=0;i<sparse.count;i++){const vertex=readComponent(view,(indices.byteOffset??0)+(sparse.indices.byteOffset??0)+i*indexSize,sparse.indices.componentType);if(vertex>=accessor.count)throw new Error('Sparse weight index exceeds accessor length.');for(let channel=0;channel<4;channel++)values[vertex*4+channel]=readComponent(view,(replacement.byteOffset??0)+(sparse.values.byteOffset??0)+(i*4+channel)*size,accessor.componentType);}}
  return values;
}
/** Installed Babylon glTF loader supports at most JOINTS/WEIGHTS sets 0 and 1. */
export function inspectSkinInfluences(gltf:GltfDocument,binary:Uint8Array):SkinInfluenceInventory{
  const issues:string[]=[],primitives:SkinInfluenceInventory['primitives']=[];
  for(const [meshIndex,mesh] of (gltf.meshes??[]).entries())for(const [primitiveIndex,primitive] of mesh.primitives.entries()){
    const prefix=`mesh ${meshIndex} (${mesh.name??'unnamed'}) primitive ${primitiveIndex}`;
    for(const attribute of Object.keys(primitive.attributes)){const match=/^(?:JOINTS|WEIGHTS)_(\d+)$/.exec(attribute);if(match&&Number(match[1])>=2)issues.push(`${prefix}: unsupported ${attribute}; the viewer loads at most eight bone influences (sets 0 and 1).`);}
    const weightSets=Object.keys(primitive.attributes).filter(name=>/^WEIGHTS_[01]$/.test(name)).sort();
    if(!weightSets.length)continue;
    const entry:SkinInfluenceInventory['primitives'][number]={mesh:mesh.name??`mesh_${meshIndex}`,meshIndex,primitiveIndex,weightSets,vertices:0,maxNonzeroWeights:null,meanNonzeroWeights:null,unreadableReason:null};
    try{
      const weights=weightSets.map(name=>readWeights(gltf,binary,primitive.attributes[name]));
      entry.vertices=weights[0].length/4;
      if(weights.some(values=>values.length!==weights[0].length))throw new Error('Weight-set accessor counts differ.');
      let maximum=0,total=0;
      for(let vertex=0;vertex<entry.vertices;vertex++){let count=0;for(const values of weights)for(let channel=0;channel<4;channel++)if(values[vertex*4+channel]>0)count++;maximum=Math.max(maximum,count);total+=count;}
      entry.maxNonzeroWeights=maximum;entry.meanNonzeroWeights=entry.vertices?total/entry.vertices:0;
    }catch(error){entry.unreadableReason=error instanceof Error?error.message:String(error);issues.push(`${prefix}: ${entry.unreadableReason}`);}
    primitives.push(entry);
  }
  return{issues,primitives};
}
export interface RuntimeMeshInfluence {name:string;numBoneInfluencers:number;pointers:string[];hasExtraJointBuffer?:boolean;hasExtraWeightBuffer?:boolean;}
export interface RuntimeSkinInvariant {status:'matched'|'mismatch';issues:string[];checks:{sourcePointer:string;sourceMesh:string;maximumNonzeroWeights:number;runtimeMesh:string|null;observedNumBoneInfluencers:number|null;extraJointBufferPresent:boolean|null;extraWeightBufferPresent:boolean|null;requiredNumBoneInfluencers:8;matched:boolean}[];scope:string;}
/** Post-load CPU-side invariant, deliberately distinct from successful GPU execution. */
export function checkRuntimeSkinInfluences(source:SkinInfluenceInventory,runtime:RuntimeMeshInfluence[]):RuntimeSkinInvariant{
  const issues:string[]=[],checks:RuntimeSkinInvariant['checks']=[];
  for(const primitive of source.primitives){
    if(primitive.maxNonzeroWeights===null||primitive.maxNonzeroWeights<=4)continue;
    const pointer=`/meshes/${primitive.meshIndex}/primitives/${primitive.primitiveIndex}`;
    const meshes=runtime.filter(mesh=>mesh.pointers.includes(pointer));
    if(!meshes.length){issues.push(`${primitive.mesh}: cannot resolve imported primitive ${pointer} to verify eight-weight skinning.`);checks.push({sourcePointer:pointer,sourceMesh:primitive.mesh,maximumNonzeroWeights:primitive.maxNonzeroWeights,runtimeMesh:null,observedNumBoneInfluencers:null,extraJointBufferPresent:null,extraWeightBufferPresent:null,requiredNumBoneInfluencers:8,matched:false});}
    for(const mesh of meshes){
      const modeMatches=Number.isFinite(mesh.numBoneInfluencers)&&mesh.numBoneInfluencers>=8;
      const matched=modeMatches&&mesh.hasExtraJointBuffer===true&&mesh.hasExtraWeightBuffer===true;
      checks.push({sourcePointer:pointer,sourceMesh:primitive.mesh,maximumNonzeroWeights:primitive.maxNonzeroWeights,runtimeMesh:mesh.name,observedNumBoneInfluencers:Number.isFinite(mesh.numBoneInfluencers)?mesh.numBoneInfluencers:null,extraJointBufferPresent:mesh.hasExtraJointBuffer??null,extraWeightBufferPresent:mesh.hasExtraWeightBuffer??null,requiredNumBoneInfluencers:8,matched});
      if(!modeMatches)issues.push(`${mesh.name}: delivered primitive requires ${primitive.maxNonzeroWeights} nonzero weights, but Babylon numBoneInfluencers is ${mesh.numBoneInfluencers}; at least 8 are required.`);
      if(mesh.hasExtraJointBuffer!==true)issues.push(`${mesh.name}: required extra joint buffer (MatricesIndicesExtraKind / JOINTS_1) is missing or unverified.`);
      if(mesh.hasExtraWeightBuffer!==true)issues.push(`${mesh.name}: required extra weight buffer (MatricesWeightsExtraKind / WEIGHTS_1) is missing or unverified.`);
    }
  }
  return{status:issues.length?'mismatch':'matched',issues,checks,scope:'Observed imported Babylon mesh configuration checked against delivered GLB weights. This verifies a CPU-side loader invariant, not shader execution, successful GPU rendering, or visual deformation quality.'};
}
