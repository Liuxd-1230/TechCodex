import {interpolate} from './sweep-model.mjs';
const root=document.querySelector('[data-demo="mirror-compliance"]');
if(root) start().catch(()=>{root.hidden=true;root.nextElementSibling.hidden=false;root.nextElementSibling.textContent='交互数据暂不可用，请阅读本节原图、曲线和推导。';});

async function start(){
  const response=await fetch(new URL('./mirror-data.json',import.meta.url));
  if(!response.ok)throw new Error('No data');const data=await response.json();
  if(data.schema!==1)throw new Error('Unknown data');
  const slider=root.querySelector('#mirror-voltage'),selector=root.querySelector('#mirror-topology');
  const field=Object.fromEntries([...root.querySelectorAll('[data-mirror-field]')].map(el=>[el.dataset.mirrorField,el]));
  const x=v=>55+v/3*405,y=i=>235-i*1e6/50*200;
  for(const name of ['medium','cascode'])root.querySelector(`[data-mirror-curve="${name}"]`).setAttribute('d',data.curves[name].map((p,i)=>`${i?'L':'M'}${x(p[0])} ${y(p[1])}`).join(''));
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
      if(active)svg.querySelector('desc').textContent=`${cas?'经典共源共栅镜':'普通镜'}。VO ${voltage.toFixed(3)} 伏，输出电流 ${(p[1]*1e6).toFixed(2)} 微安，${cas?`内部 X ${p[3].toFixed(3)} 伏，`:''}${saturated?'输出管均满足模型饱和条件':'至少一只输出管不满足模型饱和条件'}。所有体端接地。`;
    });
    field.cursor.setAttribute('d',`M${x(voltage)} 35V235`);field.dot.setAttribute('cx',x(voltage));field.dot.setAttribute('cy',y(p[1]));field.dot.style.fill=cas?'#a05b18':'#126e63';
    field.readout.textContent=`IO ${(p[1]*1e6).toFixed(2)} µA · 相对 40 µA 误差 ${error.toFixed(2)}% · ${cas?`M2 VDS ${p[3].toFixed(3)} V，M4 VDS ${(voltage-p[3]).toFixed(3)} V`:`M2 VDS ${voltage.toFixed(3)} V`}`;
    let note=cas?`内部 X ${p[3].toFixed(3)} V；下管饱和余量 ${bottom.toFixed(3)} V，上管 ${upper.toFixed(3)} V。`:`输出管饱和余量 ${bottom.toFixed(3)} V。`;
    note+=saturated?'当前可以使用本工作点附近的饱和区小信号解释。':'至少一只管已离开饱和，不能继续承诺饱和区的高输出电阻。';
    note+=Math.abs(error)<=5?' 电流仍在 ±5% 内；这与是否饱和是两个不同判断。':' 电流已经超出 ±5% 容差。';
    field.observation.textContent=note;
    clearTimeout(update.timer);update.timer=setTimeout(()=>{field.announcement.textContent=note;},150);
  }
  slider.addEventListener('input',update);selector.addEventListener('change',update);update();root.hidden=false;root.nextElementSibling.hidden=true;
  if(location.hash==='#mirror-demo-title')root.scrollIntoView({block:'start'});
}
