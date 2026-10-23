import {calculate,magnitude,angle} from './frequency-model.mjs';
const root=document.querySelector('[data-demo="miller-poles"]');
if(root){try{start();}catch{root.hidden=true;root.nextElementSibling.hidden=false;}}
function start(){
  const cap=root.querySelector('#miller-cap'),freq=root.querySelector('#miller-frequency'),overlay=root.querySelector('#miller-approx');
  const fields=Object.fromEntries([...root.querySelectorAll('[data-frequency]')].map(el=>[el.dataset.frequency,el]));
  const unit=f=>f>=1e9?`${(f/1e9).toFixed(2)} GHz`:f>=1e6?`${(f/1e6).toFixed(2)} MHz`:`${(f/1e3).toFixed(1)} kHz`;
  const amplitude=z=>magnitude(z)>=.01?magnitude(z).toFixed(3):magnitude(z).toExponential(2);
  const path=points=>points.map((p,i)=>`${i?'L':'M'}${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join('');
  function update(){
    const cf=Number(cap.value)*1e-15,f=10**(Number(freq.value)/100),state=calculate(cf,f),show=overlay.checked;
    root.querySelector('#miller-cap-value').textContent=`${cap.value} fF`;root.querySelector('#miller-frequency-value').textContent=unit(f);
    cap.setAttribute('aria-valuetext',`${cap.value} 飞法`);freq.setAttribute('aria-valuetext',unit(f));
    const lines={gain:[],phase:[],approxGain:[],approxPhase:[]};
    for(let i=0;i<=360;i++){
      const t=calculate(cf,10**(4+i/60)),x=70+i/360*500;
      lines.gain.push([x,20+(40-20*Math.log10(magnitude(t.vo)))*1.25]);lines.phase.push([x,220-t.phase*120/270]);
      lines.approxGain.push([x,20+(40-20*Math.log10(magnitude(t.approximate)))*1.25]);lines.approxPhase.push([x,220-t.approximatePhase*120/270]);
    }
    for(const [name,points] of Object.entries(lines))fields[name].setAttribute('d',name.startsWith('approx')&&!show?'':path(points));
    const x=70+(Math.log10(f)-4)/6*500;fields.cursor.setAttribute('d',`M${x} 20V340`);
    fields.gate.textContent=`vg ${amplitude(state.vg)} ∠ ${angle(state.vg).toFixed(1)}°`;
    fields.output.textContent=`vo ${amplitude(state.vo)} ∠ ${angle(state.vo).toFixed(1)}°`;
    fields.nodeValues.textContent=`栅节点 ${amplitude(state.vg)} ∠ ${angle(state.vg).toFixed(1)}°；输出 ${amplitude(state.vo)} ∠ ${angle(state.vo).toFixed(1)}°（V / V输入）。`;
    fields.capLabel.textContent=`Cgd ${cap.value} fF`;
    const across=Math.hypot(state.vg[0]-state.vo[0],state.vg[1]-state.vo[1]);
    fields.coupling.textContent=`Cgd 两端压差 ${across.toFixed(3)} V / V输入，约为栅节点幅值的 ${(across/magnitude(state.vg)).toFixed(1)} 倍；跨端电流 ${(magnitude(state.current)*1e6).toFixed(2)} µA / V输入。`;
    root.querySelector('.signal-coupling').style.opacity=cf===0?'.25':'1';
    fields.readout.textContent=`极点 ${unit(state.slowHz)}、${unit(state.fastHz)} · RHP 零点 ${state.zeroHz?unit(state.zeroHz):'无有限值'}。观察点：${(20*Math.log10(magnitude(state.vo))).toFixed(2)} dB，附加相移 ${state.phase.toFixed(1)}°；跨端电流 ${(magnitude(state.current)*1e6).toFixed(2)} µA / V输入。`;
    const relative=Math.abs(magnitude(state.approximate)/magnitude(state.vo)-1)*100;
    fields.admittance.textContent=`低频米勒输入电容 ${(state.millerInput*1e12).toFixed(2)} pF；当前 Im(Yin)/ω = ${(state.storageInput*1e12).toFixed(2)} pF，Re(Yin) = ${(state.conductanceInput*1e6).toFixed(2)} µS。`;
    const note=cf===0?'Cgd 归零后，这条跨端电流路径消失，Ci 和 Co 仍然储存电荷。加回电容，看它两端的压差为何比栅节点本身的变化更大。':f<state.slowHz/10?'低频时输出近似反相，电容两端的变化相加。输入源要经 RS 额外供应这股充放电电流，栅节点更难跟上输入。':`此频率下节点相位已改变，请把压差作为相量相减。固定低频米勒近似的幅度误差为 ${relative.toFixed(1)}%；勾选对照，观察相位和零点附近的分离。`;
    fields.observation.textContent=note;clearTimeout(update.timer);update.timer=setTimeout(()=>{fields.announcement.textContent=note;},180);
  }
  for(const el of [cap,freq])el.addEventListener('input',update);overlay.addEventListener('change',update);
  update();root.hidden=false;root.nextElementSibling.hidden=true;
  if(location.hash==='#miller-demo-title')root.scrollIntoView({block:'start'});
}
