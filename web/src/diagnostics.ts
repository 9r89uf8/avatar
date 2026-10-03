/** Local-only observation helpers. No network, browser probes, or invented performance budgets. */
export type DiagnosticValue = string | number | boolean | null | DiagnosticValue[] | { [key:string]:DiagnosticValue };
export interface NumericSummary { count:number; minimum:number|null; mean:number|null; median:number|null; p95:number|null; p99:number|null; maximum:number|null; }
export interface FrameCaptureResult {
  status:'completed'|'cancelled'; reason:string; requestedDurationMs:number; observedDurationMs:number;
  renderedFrames:number; renderedFramesPerObservedSecond:number|null; timerOverrunMs:number; timeAfterLastFrameMs:number; rejectedIntervals:number; intervalDurationMs:number; averageFps:number|null;
  frameTimeMs:NumericSummary; drawCalls:NumericSummary; frameIntervalsMs:number[]; drawCallsPerFrame:(number|null)[];
  stateTimeline:{elapsedMs:number;state:DiagnosticValue}[]; omittedStateChanges:number;
  interpretation:string;
}
export interface CaptureRuntime { now:()=>number; schedule:(callback:()=>void,delayMs:number)=>unknown; cancel:(handle:unknown)=>void; }
const nativeRuntime:CaptureRuntime={now:()=>performance.now(),schedule:(callback,delay)=>setTimeout(callback,delay),cancel:handle=>clearTimeout(handle as ReturnType<typeof setTimeout>)};
const clone=<T>(value:T):T=>JSON.parse(JSON.stringify(value)) as T;
export function percentile(sortedValues:readonly number[],fraction:number):number|null {
  if(!sortedValues.length)return null;
  const position=Math.max(0,Math.min(1,fraction))*(sortedValues.length-1);
  const lower=Math.floor(position),upper=Math.ceil(position);
  return sortedValues[lower]+(sortedValues[upper]-sortedValues[lower])*(position-lower);
}
export function summarize(values:readonly number[]):NumericSummary {
  const sorted=values.filter(Number.isFinite).slice().sort((a,b)=>a-b);
  return {count:sorted.length,minimum:sorted[0]??null,mean:sorted.length?sorted.reduce((a,b)=>a+b,0)/sorted.length:null,median:percentile(sorted,.5),p95:percentile(sorted,.95),p99:percentile(sorted,.99),maximum:sorted.at(-1)??null};
}
export function formatCaptureSummary(result:FrameCaptureResult):string {
  if(result.status==='cancelled')return `Capture cancelled: ${result.reason}. No performance verdict was assigned.`;
  if(result.averageFps===null||result.frameTimeMs.median===null||result.frameTimeMs.p95===null)return 'No usable frame intervals were observed. The report contains capability and state information only.';
  return `${result.averageFps.toFixed(1)} interval-average FPS; median ${result.frameTimeMs.median.toFixed(2)} ms, 95th percentile ${result.frameTimeMs.p95.toFixed(2)} ms across ${result.frameTimeMs.count} intervals. These are observations, not a pass/fail verdict.`;
}
/** A bounded, cancellable sampler driven by real completed-render timestamps. */
export class FrameCapture {
  private running=false;
  private disposed=false;
  private timer:unknown;
  private started=0;
  private previous:number|null=null;
  private intervals:number[]=[];
  private draws:(number|null)[]=[];
  private states:{elapsedMs:number;state:DiagnosticValue}[]=[];
  private stateKey='';
  private omittedStates=0;
  private rejected=0;
  private callback:((result:FrameCaptureResult)=>void)|null=null;
  readonly durationMs:number;
  private runtime:CaptureRuntime;
  constructor(durationMs=10000,runtime:CaptureRuntime=nativeRuntime){
    this.runtime=runtime;
    if(!Number.isFinite(durationMs)||durationMs<1000||durationMs>30000)throw new Error('Capture duration must be between 1 and 30 seconds.');
    this.durationMs=durationMs;
  }
  get active():boolean{return this.running;}
  get remainingMs():number{return this.running?Math.max(0,this.durationMs-(this.runtime.now()-this.started)):0;}
  start(state:DiagnosticValue,callback:(result:FrameCaptureResult)=>void):void {
    if(this.disposed)throw new Error('The diagnostic sampler has been disposed.');
    if(this.running)throw new Error('A diagnostic capture is already in progress.');
    this.running=true;this.started=this.runtime.now();this.previous=null;this.intervals=[];this.draws=[];this.states=[];this.stateKey='';this.omittedStates=0;this.rejected=0;this.callback=callback;
    this.recordState(this.started,state);
    this.timer=this.runtime.schedule(()=>this.finish('completed','observation-window-complete'),this.durationMs);
  }
  record(timestamp:number,drawCalls:number,state:DiagnosticValue):void {
    if(!this.running)return;
    if(!Number.isFinite(timestamp)||timestamp<this.started||(this.previous!==null&&timestamp<=this.previous)){this.rejected++;return;}
    if(timestamp-this.started>this.durationMs){this.finish('completed','observation-window-complete');return;}
    if(this.draws.length>=30000){this.finish('cancelled','sample-capacity-reached');return;}
    if(this.previous!==null)this.intervals.push(timestamp-this.previous);
    this.previous=timestamp;
    this.draws.push(Number.isFinite(drawCalls)&&drawCalls>=0?drawCalls:null);
    this.recordState(timestamp,state);
  }
  private recordState(timestamp:number,state:DiagnosticValue):void {
    const key=JSON.stringify(state);
    if(key===this.stateKey)return;
    this.stateKey=key;
    if(this.states.length<128)this.states.push({elapsedMs:Math.max(0,timestamp-this.started),state:clone(state)});
    else this.omittedStates++;
  }
  cancel(reason='user-cancelled'):void {this.finish('cancelled',reason);}
  reset():void {this.cancel('viewer-reset');}
  dispose():void {if(this.disposed)return;this.cancel('viewer-disposed');this.disposed=true;}
  private finish(status:'completed'|'cancelled',reason:string):void {
    if(!this.running)return;
    this.running=false;this.runtime.cancel(this.timer);this.timer=undefined;
    const total=this.intervals.reduce((sum,value)=>sum+value,0);
    const finished=this.runtime.now(),observed=Math.max(0,finished-this.started);
    const result:FrameCaptureResult={status,reason,requestedDurationMs:this.durationMs,observedDurationMs:observed,renderedFrames:this.draws.length,renderedFramesPerObservedSecond:observed>0?1000*this.draws.length/observed:null,timerOverrunMs:Math.max(0,observed-this.durationMs),timeAfterLastFrameMs:this.previous===null?observed:Math.max(0,finished-this.previous),rejectedIntervals:this.rejected,intervalDurationMs:total,averageFps:total>0?1000*this.intervals.length/total:null,frameTimeMs:summarize(this.intervals),drawCalls:summarize(this.draws.filter((value):value is number=>value!==null)),frameIntervalsMs:[...this.intervals],drawCallsPerFrame:[...this.draws],stateTimeline:clone(this.states),omittedStateChanges:this.omittedStates,interpretation:'Intervals between completed browser render callbacks, including scheduling and CPU/GPU waits. Interval-average FPS excludes gaps before the first and after the last completed frame. Whole-observation frame throughput, trailing gap and timer overrun are also reported so a final stall is not hidden. Not isolated GPU timings, cold-load timings, or a device certification. No performance budget has been assumed.'};
    const callback=this.callback;this.callback=null;this.previous=null;this.intervals=[];this.draws=[];this.states=[];this.stateKey='';
    callback?.(result);
  }
}
export function serializeDiagnostic(report:unknown):string{return JSON.stringify(report,null,2)+'\n';}
