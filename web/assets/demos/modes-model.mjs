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

export function modeObservation(kind,s){
  if(s.vi1===0&&s.vi2===0)return '输入增量为零，各节点与支路都保持原工作点。';
  if(kind==='differential')return '对称差模下，支路一增一减，尾节点无需改变。';
  if(s.rt===Infinity)return kind==='unequal'
    ? '理想尾源下，尾节点的移动恰好使两支路电流增量都为零；不等负载也没有增量电流可转换，因此输出差仍为零。'
    : '理想尾源下，尾节点随共同输入移动，两支路电流与输出的增量都为零。';
  return kind==='unequal'
    ? '有限尾阻抗允许共同输入改变支路电流；不等负载把它们转换为不同的输出电压，产生输出差。'
    : '尾节点移动；两边输出相同，相减仍为零。';
}
