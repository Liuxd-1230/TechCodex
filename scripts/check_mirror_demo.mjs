import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {interpolate} from '../web/assets/demos/sweep-model.mjs';
const data=JSON.parse(readFileSync(new URL('../web/assets/demos/mirror-data.json',import.meta.url)));
for(const [name,rows] of Object.entries(data.curves)){
  assert.equal(rows.length,296);
  for(let i=0;i<rows.length;i++){
    assert.deepEqual(interpolate(rows[i][0],rows),rows[i]);
    if(i){
      const midpoint=interpolate((rows[i][0]+rows[i-1][0])/2,rows);
      midpoint.forEach((v,k)=>assert.ok(Math.abs(v-(rows[i][k]+rows[i-1][k])/2)<1e-12));
    }
  }
  assert.throws(()=>interpolate(.01,rows),RangeError);assert.throws(()=>interpolate(3.01,rows),RangeError);
  const p=interpolate(.4,rows);
  assert.ok(Math.abs(p[1]/40e-6-1)<.05,'At 0.4 V both mirrors still meet current tolerance');
  if(name==='cascode') assert.ok(.4-p[3]<p[5],'But cascode upper MOS has left saturation');
  else assert.ok(p[3]>p[4]);
}
console.log('PASS: both 296-point sweeps, midpoints, bounds, and current-tolerance versus saturation distinction.');
