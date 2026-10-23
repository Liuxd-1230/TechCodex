import assert from 'node:assert/strict';
import {calculate,magnitude} from '../web/assets/demos/frequency-model.mjs';
const mul=(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]],sum=(...zs)=>zs.reduce((a,b)=>[a[0]+b[0],a[1]+b[1]],[0,0]);
let count=0;
for(let cap=0;cap<=1000;cap+=10)for(let log=4;log<=10;log+=.25){
  const cf=cap*1e-15,w=2*Math.PI*10**log,r=calculate(cf,10**log);
  assert(magnitude(sum(mul([1e-4,w*(1e-12+cf)],r.vg),mul([0,-w*cf],r.vo),[-1e-4,0]))<1e-12);
  assert(magnitude(sum(mul([1e-3,-w*cf],r.vg),mul([2e-5,w*(1e-12+cf)],r.vo)))<1e-12);
  assert(r.slowHz>0&&r.fastHz>=r.slowHz);assert(r.phase<=0&&r.phase>=-270);count++;
}
assert.equal(calculate(0,1e4).zeroHz,null);assert.throws(()=>calculate(-1,1e6),RangeError);assert.throws(()=>calculate(1e-12,1e11),RangeError);
console.log(`PASS: ${count} states, independent complex KCL, stable poles, zero at infinity, bounds.`);
