import {interpolate} from './sweep-model.mjs';
const root=document.querySelector('[data-demo="mirror-compliance"]');
if(root) start().catch(()=>{root.hidden=true;root.nextElementSibling.hidden=false;root.nextElementSibling.textContent='交互数据暂不可用，请阅读本节原图、曲线和推导。';});

const SVG_NS='http://www.w3.org/2000/svg';
const OUTPUT_DEVICES={medium:[['M2',250]],cascode:[['M2',440],['M4',240]]};

async function start(){
  const response=await fetch(new URL('./mirror-data.json',import.meta.url));
  if(!response.ok)throw new Error('No data');const data=await response.json();
  if(data.schema!==1)throw new Error('Unknown data');
  const slider=root.querySelector('#mirror-voltage'),selector=root.querySelector('#mirror-topology');
  const field=Object.fromEntries([...root.querySelectorAll('[data-mirror-field]')].map(el=>[el.dataset.mirrorField,el]));
  const x=v=>55+v/3*405,y=i=>235-i*1e6/50*200;
  const outlines={};
  for(const name of ['medium','cascode']){
    const svg=root.querySelector(`[data-topology="${name}"]`);
    outlines[name]={};
    for(const [device,centerY] of OUTPUT_DEVICES[name]){
      const rect=document.createElementNS(SVG_NS,'rect');
      rect.setAttribute('class','demo-device-outline');
      rect.setAttribute('data-device',device);
      rect.setAttribute('data-state','valid');
      rect.setAttribute('aria-hidden','true');
      rect.setAttribute('x','416');rect.setAttribute('y',String(centerY-40));
      rect.setAttribute('width','80');rect.setAttribute('height','80');rect.setAttribute('rx','4');
      rect.setAttribute('fill','none');
      svg.insertBefore(rect,svg.querySelector('g'));
      outlines[name][device]=rect;
    }
    root.querySelector(`[data-mirror-curve="${name}"]`).setAttribute('d',data.curves[name].map((p,i)=>`${i?'L':'M'}${x(p[0])} ${y(p[1])}`).join(''));
  }
  function update(){
    const voltage=Number(slider.value)/1000,name=selector.value,cas=name==='cascode';
    const p=interpolate(voltage,data.curves[name]);
    const bottom=p[3]-p[4],upper=cas?voltage-p[3]-p[5]:null;
    const saturated=bottom>=0&&(!cas||upper>=0),error=(p[1]/40e-6-1)*100;
    field.voltage.textContent=`${voltage.toFixed(3)} V`;slider.setAttribute('aria-valuetext',`${voltage.toFixed(3)} 伏`);
    root.querySelectorAll('[data-topology]').forEach(svg=>{
      const active=svg.dataset.topology===name;svg.toggleAttribute('hidden',!active);
      const values={output:`${voltage.toFixed(3)} V`,gate:`VB ${p[2].toFixed(3)} V`,internal:`${p[3].toFixed(3)} V`};
      svg.querySelectorAll('[data-mirror-node]').forEach(el=>{el.textContent=values[el.dataset.mirrorNode];});
    });
    field.cursor.setAttribute('d',`M${x(voltage)} 35V235`);field.dot.setAttribute('cx',x(voltage));field.dot.setAttribute('cy',y(p[1]));field.dot.style.fill=cas?'#a05b18':'#126e63';
    field.readout.textContent=`IO ${(p[1]*1e6).toFixed(2)} µA · 相对 40 µA 误差 ${error.toFixed(2)}%`;
    const margins=cas?[['M2',bottom],['M4',upper]]:[['M2',bottom]];
    for(const [device,margin] of margins)outlines[name][device].setAttribute('data-state',margin<0?'invalid':'valid');
    field['device-state'].textContent=margins.map(([device,margin])=>`${device} ${margin<0?'未饱和（线性区）':'饱和'} · VDS−VDSAT ${margin>0?'+':''}${margin.toFixed(3)} V`).join('　·　');
    const state=cas?`M2 ${bottom<0?'已离开饱和':'饱和'}，M4 ${upper<0?'已离开饱和':'饱和'}`:`M2 ${bottom<0?'已离开饱和':'饱和'}`;
    const regime=saturated?'输出管满足模型饱和条件。':'至少一只输出管进入线性区；饱和区高输出电阻近似不再适用。';
    const tolerance=Math.abs(error)<=5?'电流仍在 ±5% 内。':'电流已超出 ±5% 容差。';
    const note=`${state}。${regime} ${tolerance}`;
    for(const svg of root.querySelectorAll('[data-topology]'))if(svg.dataset.topology===name){
      svg.querySelector('desc').textContent=`${cas?'经典共源共栅镜':'普通镜'}。VO ${voltage.toFixed(3)} 伏，输出电流 ${(p[1]*1e6).toFixed(2)} 微安；${margins.map(([device,margin])=>`${device} ${margin<0?'未饱和':'饱和'}，VDS−VDSAT ${margin.toFixed(3)} 伏`).join('；')}。所有体端接地。`;
    }
    field.observation.textContent=note;
    clearTimeout(update.timer);update.timer=setTimeout(()=>{field.announcement.textContent=note;},150);
  }
  slider.addEventListener('input',update);selector.addEventListener('change',update);update();root.hidden=false;root.nextElementSibling.hidden=true;
  if(location.hash==='#mirror-demo-title')root.scrollIntoView({block:'start'});
}
