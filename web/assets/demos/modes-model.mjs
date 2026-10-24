/* Fixed-bias low-frequency three-parameter MOS model; v and i are increments.
 * RD=40k; gm=.3mS, gmb=.1mS, go=1uS. RT is tail output resistance,
 * not a resistor that establishes the DC tail current. No transient is solved.
 */
export function modes(kind,input,rt){
  if(!['differential','common','unequal'].includes(kind)||!Number.isFinite(input)||Math.abs(input)>.01||![10000,100000,Infinity].includes(rt))throw RangeError('Outside the mode example');
  const gm=.0003,gmb=.0001,go=.000001,k=gm+gmb+go;
  const r1=40000,r2=kind==='unequal'?44000:40000,g1=1/r1,g2=1/r2;
  const vi1=kind==='differential'?input/2:input,vi2=kind==='differential'?-input/2:input;
  const a1=gm/(g1+go),a2=gm/(g2+go),b1=k/(g1+go),b2=k/(g2+go);
  const vt=(g1*a1*vi1+g2*a2*vi2)/(1/rt+g1*b1+g2*b2);
  const vo1=b1*vt-a1*vi1,vo2=b2*vt-a2*vi2,i1=-g1*vo1,i2=-g2*vo2,it=vt/rt;
  return {gm,gmb,go,r1,r2,rt,vi1,vi2,vt,vo1,vo2,i1,i2,it,vod:vo1-vo2};
}
