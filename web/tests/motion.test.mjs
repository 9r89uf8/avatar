import test from 'node:test';
import assert from 'node:assert/strict';
import {blinkAt,clamp,damp,faceFrame,gazeAt} from '../src/motion.ts';
test('blink stays physically bounded over 120 seconds',()=>{let closed=0;for(let t=0;t<120;t+=.001){const v=blinkAt(t);assert.ok(v>=0&&v<=1,`out of bounds at ${t}`);if(v>.99)closed++;}assert.ok(closed>0);});
test('blink has closing, contact and slower opening phases',()=>{assert.equal(blinkAt(-.42),0);assert.equal(blinkAt(-.42+.11),1);assert.ok(blinkAt(-.42+.2)>0);assert.equal(blinkAt(-.42+.3),0);});
test('damping is independent of frame subdivision',()=>{let value=0;for(let i=0;i<60;i++)value=damp(value,1,6,1/60);assert.ok(Math.abs(value-damp(0,1,6,1))<1e-12);});
test('damping never overshoots',()=>{for(let dt=0;dt<2;dt+=.01)assert.ok(damp(0,1,10,dt)>=0&&damp(0,1,10,dt)<=1);});
test('frame inference respects source bounds and meter scale',()=>{const frame=faceFrame([-.5,0,-.2],[.5,1.6,.2]);assert.equal(frame.height,1.6);assert.equal(frame.centerX,0);assert.equal(frame.centerZ,0);assert.ok(frame.headY>1.4&&frame.headY<1.5);});
test('clamp limits head and morph inputs',()=>{assert.equal(clamp(2,0,1),1);assert.equal(clamp(-1,0,1),0);assert.equal(clamp(.5,0,1),.5);});

test('microgaze is bounded to small human-scale angles',()=>{for(let t=0;t<180;t+=.002){const gaze=gazeAt(t);assert.ok(Math.abs(gaze.yaw)<=2);assert.ok(Math.abs(gaze.pitch)<=1);}});
test('microgaze is deterministic and has long holds',()=>{assert.deepEqual(gazeAt(5),gazeAt(5));assert.deepEqual(gazeAt(5),gazeAt(7));assert.notDeepEqual(gazeAt(5),gazeAt(10));});
test('microgaze transitions continuously between held targets',()=>{for(let t=.01;t<120;t+=.01){const a=gazeAt(t),b=gazeAt(t-.01);assert.ok(Math.abs(a.yaw-b.yaw)<.12);assert.ok(Math.abs(a.pitch-b.pitch)<.06);}});
