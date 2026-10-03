/** Deterministic, bounded motion. Times are simulation seconds, not wall time. */
export function blinkAt(t:number):number {
  const phase = ((t + 0.42) % 4.7);
  if (phase < 0.095) return Math.sin((phase / 0.095) * Math.PI * 0.5);
  if (phase < 0.13) return 1;
  if (phase < 0.285) return Math.cos(((phase - 0.13) / 0.155) * Math.PI * 0.5);
  return 0;
}
export function damp(current:number,target:number,rate:number,dt:number):number { return current + (target-current)*(1-Math.exp(-rate*dt)); }
export function clamp(value:number,min:number,max:number):number { return Math.max(min,Math.min(max,value)); }
export function faceFrame(min:[number,number,number],max:[number,number,number]) {
  const height=max[1]-min[1];
  const centerZ=(min[2]+max[2])/2;
  return {height, centerZ, headY:min[1]+height*0.902, centerX:(min[0]+max[0])/2};
}

/** Shared binocular microgaze in degrees. Each saccade is followed by a long hold. */
export function gazeAt(time:number):{yaw:number;pitch:number} {
  const stops=[
    {duration:3.8,yaw:0,pitch:0},
    {duration:4.6,yaw:1.55,pitch:-0.45},
    {duration:3.2,yaw:-1.15,pitch:0.65},
    {duration:5.1,yaw:0.4,pitch:0.15},
    {duration:3.7,yaw:-1.8,pitch:-0.55},
    {duration:4.4,yaw:0.9,pitch:-0.15},
    {duration:5.6,yaw:0,pitch:0},
  ];
  const total=stops.reduce((sum,stop)=>sum+stop.duration,0);
  let phase=((time%total)+total)%total;
  for(let index=0;index<stops.length;index++){
    const stop=stops[index];
    if(phase<stop.duration){
      const previous=stops[(index+stops.length-1)%stops.length];
      const ratio=clamp(phase/0.52,0,1);const ease=ratio*ratio*(3-2*ratio);
      return {yaw:previous.yaw+(stop.yaw-previous.yaw)*ease,pitch:previous.pitch+(stop.pitch-previous.pitch)*ease};
    }
    phase-=stop.duration;
  }
  return{yaw:0,pitch:0};
}
