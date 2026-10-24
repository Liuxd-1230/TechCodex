import assert from 'node:assert/strict';
import {channel,channelFigure,BETA,VTH} from '../web/assets/demos/channel-model.mjs';
import {modes,modeObservation} from '../web/assets/demos/modes-model.mjs';
const close=(a,b,t=1e-8)=>assert.ok(Math.abs(a-b)<=1e-15+t*Math.max(Math.abs(a),Math.abs(b)),`${a} != ${b}`);
let count=0;
// Inspect the actual SVG curve and cursor at every allowed slider setting.
for(let gate=80;gate<=140;gate++){
  const svg=channelFigure(gate/100,1.2);
  const d=svg.match(/<path d="([^"]+)" stroke="#126e63" fill="none"/)[1];
  for(const pair of d.matchAll(/[ML]([\d.]+) ([\d.]+)/g)){
    assert.ok(+pair[1]>=64&&+pair[1]<=436&&+pair[2]>=345&&+pair[2]<=480,`Curve outside plot: ${pair[0]}`);
  }
  for(let drain=0;drain<=120;drain++){
    const figure=channelFigure(gate/100,drain/100);
    const cursor=figure.match(/<circle cx="([^"]+)" cy="([^"]+)"/);
    assert.ok(+cursor[1]>=64&&+cursor[1]<=436&&+cursor[2]>=345&&+cursor[2]<=480);
  }
}
close(channel(1.4,.8).id,64e-6);close(channel(1.4,1.2).id,64e-6);
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
  if(kind!=='differential'&&rt===Infinity){
    close(s.vo1,0);close(s.vo2,0);close(s.i1,0);close(s.i2,0);close(s.vt,s.gm*input/k);
    if(input!==0)assert.match(modeObservation(kind,s),/都为零/);
  }
  if(input===0)assert.match(modeObservation(kind,s),/输入增量为零/);
  if(kind==='unequal'&&rt!==Infinity&&input!==0){
    assert.ok(Math.abs(s.vod)>1e-6);assert.match(modeObservation(kind,s),/有限尾阻抗/);
  }
  count++;
}
console.log(`PASS: 7381 slider positions stay inside the plot; ${count} channel drift-current and independent three-node mode checks.`);
