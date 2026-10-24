import assert from 'node:assert/strict';
import {channel,BETA,VTH} from '../web/assets/demos/channel-model.mjs';
import {modes} from '../web/assets/demos/modes-model.mjs';
const close=(a,b,t=1e-8)=>assert.ok(Math.abs(a-b)<=1e-15+t*Math.max(Math.abs(a),Math.abs(b)),`${a} != ${b}`);
let count=0;
for(const vg of [.8,1,1.4])for(const vd of [0,.1,.2,.4,.8,1.2]){
  const s=channel(vg,vd),ov=vg-VTH;
  close(s.id,vd<ov?BETA*(ov*vd-vd*vd/2):BETA*ov*ov/2);
  close(channel(vg,vd,0).q,ov);assert.ok(s.q>=0);
  if(s.saturated)close(s.q,0);
  // Independent spatial finite-difference check of constant drift current.
  for(const u of [.01,.2,.5,.8,.95]){
    const h=1e-5,dVdu=(channel(vg,vd,u+h).potential-channel(vg,vd,u-h).potential)/(2*h);
    close(BETA*channel(vg,vd,u).q*dVdu,s.id,1e-6);count++;
  }
}
// Solve the original three-node equations independently of the closed form.
function solve(a,b){
  const m=a.map((r,i)=>[...r,b[i]]);
  for(let c=0;c<3;c++){
    const v=m[c][c];m[c]=m[c].map(x=>x/v);
    for(let r=0;r<3;r++)if(r!==c){const q=m[r][c];m[r]=m[r].map((x,i)=>x-q*m[c][i]);}
  }
  return m.map(r=>r[3]);
}
for(const kind of ['differential','common','unequal'])for(const input of [-.01,0,.01])for(const rt of [1e4,1e5,Infinity]){
  const s=modes(kind,input,rt),g1=1/s.r1,g2=1/s.r2,k=s.gm+s.gmb+s.go;
  const [o1,o2,t]=solve([[g1+s.go,0,-k],[0,g2+s.go,-k],[g1,g2,1/rt]],[-s.gm*s.vi1,-s.gm*s.vi2,0]);
  close(s.vo1,o1);close(s.vo2,o2);close(s.vt,t);close(s.i1+s.i2,s.it,1e-6);
  if(kind==='differential')close(s.vt,0);
  if(kind==='common')close(s.vod,0);
  if(kind==='common'&&rt===Infinity){close(s.vo1,0);close(s.vt,s.gm*input/k);}
  count++;
}
console.log(`PASS: ${count} channel drift-current and independent three-node mode checks.`);
