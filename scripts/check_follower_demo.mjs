import assert from 'node:assert/strict';
import {END_TIME,SCENARIOS,parameters,response} from '../web/assets/demos/follower-model.mjs';

const close=(actual,expected,tolerance=1e-10)=>assert.ok(Math.abs(actual-expected)<=tolerance*Math.max(1e-12,Math.abs(expected)),`${actual} != ${expected}`);
const inputs=[-.01,-.005,0,.005,.01];
const times=[0,1e-9,10e-9,50e-9,100e-9,300e-9,END_TIME];
const dt=.25e-9;

function rk4(time,input,p){
  const steps=Math.round(time/dt);
  close(steps*dt,time,1e-12);
  let vo=0;
  const slope=value=>(p.gm*input-p.go*value)/p.C;
  for(let i=0;i<steps;i++){
    const k1=slope(vo),k2=slope(vo+dt*k1/2),k3=slope(vo+dt*k2/2),k4=slope(vo+dt*k3);
    vo+=dt*(k1+2*k2+2*k3+k4)/6;
  }
  return vo;
}

let cases=0;
for(const key of Object.keys(SCENARIOS)){
  const p=parameters(key);
  for(const input of inputs){
    for(const time of times){
      const r=response(time,input,key),reference=rk4(time,input,p);
      close(r.vo,reference,2e-9);
      close(r.id,r.ib+r.il+r.ic,2e-12);
      close(r.q,p.C*r.vo,1e-12);
      close(r.vgs,input-r.vo,1e-12);
      if(time===0){
        close(r.vo,0,1e-12);close(r.q,0,1e-12);
        close(r.ic,p.gm*input,1e-12);close(r.id,p.gm*input,1e-12);
      }
      const opposite=response(time,-input,key);
      for(const name of ['vi','vo','vgs','id','ib','il','ic','q','target','dvdt'])close(r[name],-opposite[name],2e-12);
      cases++;
    }
  }
}

const open=parameters('body'),load10k=parameters('load10k'),load1k=parameters('load1k');
close(load10k.gain,open.gain*10e3/(open.rout+10e3),1e-12);
assert(load10k.gain<open.gain&&load1k.gain<load10k.gain);
assert(load10k.tau<open.tau&&load1k.tau<load10k.tau);
assert.throws(()=>parameters('missing'),RangeError);
assert.throws(()=>response(-1,1e-3,'ideal'),RangeError);
assert.throws(()=>response(END_TIME+1,1e-3,'ideal'),RangeError);
assert.throws(()=>response(0,.011,'ideal'),RangeError);
console.log(`PASS: ${cases} RK4/KCL/symmetry checks; open-circuit loading relation and scenario trends.`);
