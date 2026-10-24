/* Long-channel strong-inversion, gradual-channel, constant mobility, lambda=0.
 * q=|Qi|/Cox in volts; its drawn depth is a charge scale, not physical thickness.
 * Beyond pinch-off the model holds the channel drop at VOV. It does not predict
 * the length of the high-field region or the potential inside that region.
 */
export const VTH=.6, BETA=200e-6;
export function channel(vgs,vds,u=1){
  if(!(vgs>=.8&&vgs<=1.4&&vds>=0&&vds<=1.2&&u>=0&&u<=1))throw RangeError('Outside the channel example');
  const ov=vgs-VTH,d=Math.min(vds,ov),drive=2*ov*d-d*d;
  const q=Math.sqrt(Math.max(0,ov*ov-drive*u));
  return {ov,q,potential:ov-q,id:BETA*drive/2,saturated:vds>=ov};
}
const path=points=>points.map(([x,y],i)=>`${i?'L':'M'}${x.toFixed(2)} ${y.toFixed(2)}`).join('');
export function channelFigure(vgs,vds,prefix='channel'){
  const s=channel(vgs,vds),q0=channel(vgs,vds,0).q;
  const profile=Array.from({length:101},(_,i)=>[80+i*3.2,156+channel(vgs,vds,i/100).q*75]);
  // The full control range reaches 64 µA; a fixed 0–80 scale preserves comparisons.
  const currentY=id=>480-id*1e6*135/80;
  const curve=Array.from({length:121},(_,i)=>[64+i*3.1,currentY(channel(vgs,i/100).id)]);
  const cx=64+vds/1.2*372,cy=currentY(s.id);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 540" role="img" aria-labelledby="${prefix}-title ${prefix}-desc">
  <title id="${prefix}-title">漏端电荷与输出电流</title><desc id="${prefix}-desc">VGS ${vgs.toFixed(2)} 伏，VDS ${vds.toFixed(2)} 伏，${s.saturated?'饱和区':'三极区'}，漏电流 ${(s.id*1e6).toFixed(2)} 微安。绿色带的深度表示反型电荷幅值，不是沟道厚度。</desc>
  <style>text{font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif;fill:#173c50;font-size:20px}path,line{vector-effect:non-scaling-stroke}</style>
  <rect width="480" height="540" fill="white"/>
  <text x="24" y="30">沿沟道：电势升高，反型电荷减少</text>
  <rect x="80" y="75" width="320" height="30" fill="#eff4f8" stroke="#566976"/>
  <text x="240" y="97" text-anchor="middle">G · ${vgs.toFixed(2)} V</text>
  <path d="M80 118H400M80 126H400" fill="none" stroke="#9b5b18"/>
  <rect x="40" y="156" width="400" height="96" fill="#eff4f8" stroke="#566976"/>
  <path d="${path([[80,156],[400,156],...profile.toReversed()])}Z" fill="#c4e3db" stroke="#126e63" stroke-width="2"/>
  <rect x="40" y="156" width="40" height="42" fill="#d8e3eb" stroke="#566976"/>
  <rect x="400" y="156" width="40" height="42" fill="#d8e3eb" stroke="#566976"/>
  <text x="50" y="147">S</text><text x="405" y="147">D</text>
  <text x="80" y="64" font-size="18">S = B = 0</text><text x="400" y="64" text-anchor="end" font-size="18">D = ${vds.toFixed(2)} V</text>
  <text x="88" y="242" font-size="18">p 型体区 · 概念截面</text>
  <text x="24" y="285" font-size="18">|Qi|/Cox：源 ${q0.toFixed(2)} V → 漏 ${s.q.toFixed(2)} V</text>
  <text x="24" y="314" fill="#126e63" font-size="19">${s.saturated?'漏端反型电荷趋零，电流仍然存在。':'漏压升高，整条沟道上的电荷分布也改变。'}</text>
  <path d="M64 345V480H436" fill="none" stroke="#173c50"/>
  <text x="436" y="338" text-anchor="end" font-size="18">ID / µA</text>
  <g stroke="#d5e0e8" fill="none"><path d="M64 412.5H436M64 345H436"/></g>
  <text x="52" y="486" text-anchor="end" font-size="17">0</text><text x="52" y="418.5" text-anchor="end" font-size="17">40</text><text x="52" y="351" text-anchor="end" font-size="17">80</text>
  <path d="M${64+s.ov/1.2*372} 350V480" stroke="#9b5b18" stroke-dasharray="4 4" fill="none"/>
  <path d="${path(curve)}" stroke="#126e63" fill="none" stroke-width="2.5"/>
  <path d="M${cx} 480V${cy}H64" stroke="#315bc5" stroke-dasharray="3 4" fill="none"/>
  <circle cx="${cx}" cy="${cy}" r="5" fill="#315bc5"/>
  <text x="64" y="506" text-anchor="middle" font-size="18">0</text><text x="250" y="506" text-anchor="middle" font-size="18">0.6</text><text x="436" y="506" text-anchor="middle" font-size="18">1.2</text>
  <text x="250" y="533" text-anchor="middle" font-size="18">VDS / V · 虚线边界 VDS = VOV</text></svg>`;
}
