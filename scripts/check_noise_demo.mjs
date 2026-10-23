import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {integrate,sample,validateRows,budget,analyticIntegral} from '../web/assets/demos/noise-model.mjs';
const near=(a,b,t=1e-10)=>assert(Math.abs(a-b)<=Math.abs(b)*t,`${a} != ${b}`);
const white=[[1,2e-16,2e-16,0],[1e6,2e-16,2e-16,0]],pink=[[1,3e-13,0,3e-13],[1e6,3e-19,0,3e-19]];
for(const [lo,hi] of [[1,1e6],[13,234567],[100,1e5]]){
  near(integrate(validateRows(white),lo,hi),2e-16*(hi-lo));near(integrate(validateRows(pink),lo,hi),3e-13*Math.log(hi/lo));
  near(analyticIntegral(lo,hi,'flicker'),1e-16*(hi-lo+1000*Math.log(hi/lo)));
}
const payload=JSON.parse(readFileSync(new URL('../web/assets/demos/noise-data.json',import.meta.url)));
const rows=validateRows(payload.rows),metrics=JSON.parse(readFileSync(new URL('../模拟/实验/噪声/data/metrics.json',import.meta.url)));
near(Math.sqrt(budget('gf',rows,100,1e5).total),metrics.baseline.bands[1].input_rms_V,1e-10);
for(let l=0;l<550;l+=5)for(let h=l+5;h<=600;h+=20){
  const b=budget('gf',rows,10**(l/100),10**(h/100));assert(b.total>0&&b.flicker>=0&&b.nonflicker>=0);near(b.total,b.flicker+b.nonflicker);
}
for(const f of [1,13,1e6])near(sample(pink,f),3e-13/f);
assert.throws(()=>integrate(rows,0,1e5),RangeError);assert.throws(()=>sample(rows,1e7),RangeError);assert.throws(()=>validateRows([[1,1,0,0],[2,1,0,1]]));
console.log('PASS: analytic white/1/f integrals, original GF RMS, all slider bands, PSD conservation and no extrapolation.');
