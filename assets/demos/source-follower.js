import {END_TIME,parameters,response} from './follower-model.mjs';

const root=document.querySelector('[data-demo="source-follower"]');
if(root) start();

function start(){
  const fields=Object.fromEntries([...root.querySelectorAll('[data-sf]')].map(el=>[el.dataset.sf,el]));
  const mode=root.querySelector('#sf-scenario'),amplitude=root.querySelector('#sf-amplitude'),seek=root.querySelector('#sf-time');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let progress=0,active=false,running=false,frame=0,started=0,announceTimer;
  const duration=2800,x=t=>40+t/END_TIME*300,y=v=>117-v*8000;
  const signed=(v,d=2)=>`${v<0?'−':v>0?'+':''}${Math.abs(v).toFixed(d)}`;
  const text=(name,value)=>{fields[name].textContent=value;};
  const path=points=>points.map(([a,b],i)=>`${i?'L':'M'}${a.toFixed(2)} ${b.toFixed(2)}`).join('');
  const input=()=>Number(amplitude.value)*1e-3;

  function announce(){
    clearTimeout(announceTimer);
    announceTimer=setTimeout(()=>text('announcement',`${fields.time.textContent}。${fields.phase.textContent}。${fields.vo.textContent}，电容电流 ${fields.ic.textContent}。`),180);
  }

  function render(){
    const t=progress*END_TIME,p=parameters(mode.value),s=response(t,active?input():0,mode.value);
    text('amplitude',`${signed(input()*1e3,0)} mV`);
    amplitude.setAttribute('aria-valuetext',`${signed(input()*1e3,0)} 毫伏`);
    text('time',active?`${(t*1e9).toFixed(1)} ns`:'阶跃前');
    seek.value=String(Math.round(progress*1000));seek.setAttribute('aria-valuetext',active?`${(t*1e9).toFixed(1)} 纳秒，${(t/p.tau).toFixed(2)} 倍时间常数`:'阶跃前，方向键开始逐点观察');
    text('vi',`vi ${signed(s.vi*1e3)} mV`);text('vo',`vo ${signed(s.vo*1e3)} mV`);
    text('vgs',`${signed(s.vgs*1e3)} mV`);text('id',`${signed(s.id*1e6)} µA`);text('ic',`${signed(s.ic*1e6)} µA`);
    text('charge',`ΔQ ${signed(s.q*1e12,3)} pC`);
    const chargeSign=s.q>0?'+':s.q<0?'−':'';
    text('top-charge',chargeSign);text('bottom-charge',chargeSign==='+'?'−':chargeSign==='−'?'+':'');
    fields['top-charge'].setAttribute('opacity',String(Math.min(1,Math.abs(s.q)/1e-12)));
    fields['bottom-charge'].setAttribute('opacity',String(Math.min(1,Math.abs(s.q)/1e-12)));
    fields['load-branch'].toggleAttribute('hidden',p.GL===0);
    text('load-label',p.GL===0?'':mode.value==='load10k'?'RL 10 kΩ':'RL 1 kΩ');
    for(const [name,current] of [['id',s.id],['ic',s.ic]]){
      fields[`${name}-arrow`].setAttribute('stroke-width',String(.6+2.4*Math.min(1,Math.abs(current)/1e-5)));
      fields[`${name}-arrow`].setAttribute('opacity',String(.15+.85*Math.min(1,Math.abs(current)/1e-5)));
    }
    fields['id-path'].setAttribute('opacity',String(.8*Math.min(1,Math.abs(s.id)/1e-5)));
    fields['ic-arrow'].setAttribute('d',s.ic<0?'M334 312V270':'M334 270V312');
    text('balance',`电流增量：δiD ${signed(s.id*1e6)} = iC ${signed(s.ic*1e6)} + δiB ${signed(s.ib*1e6)} + iL ${signed(s.il*1e6)} µA`);
    const points=Array.from({length:81},(_,i)=>{
      const time=t*i/80;return [x(time),y(response(time,active?input():0,mode.value).vo)];
    });
    fields['output-path'].setAttribute('d',path(points));
    fields['input-path'].setAttribute('d',active?`M40 117V${y(s.vi)}H340`:'M40 117H340');
    fields['target-path'].setAttribute('d',active?`M40 ${y(s.target)}H340`:'');
    fields.cursor.setAttribute('d',`M${x(t)} 22V212`);fields.point.setAttribute('cx',String(x(t)));fields.point.setAttribute('cy',String(y(s.vo)));
    fields.play.setAttribute('aria-pressed',String(running));
    text('play-label',running?'暂停观察':!active?'施加阶跃':progress>=1?'再施加一次':'继续播放');
    const tau=(p.tau*1e9).toFixed(1),target=signed(s.target*1e3,3);
    if(!active){
      text('phase','先预测，再施加阶跃');
      text('observation','电容电压需要通过电流逐渐改变。输入跳变后，哪一股电流最先改变？');
    }else if(s.vi===0){
      text('phase','输入没有改变');text('observation','阶跃幅度为零，电压、电流和电荷的增量都为零。');
    }else if(progress===0){
      text('phase','电流先改变，输出仍连续');
      text('observation',`输入已到 ${signed(s.vi*1e3)} mV，输出仍是 0 mV。最初的 ${signed(s.ic*1e6)} µA 全部流入输出电容。`);
    }else if(t<3*p.tau){
      text('phase',s.vi>0?'电容充电，输出向上跟随':'电容放电，输出向下跟随');
      text('observation',`输出变化使 |vgs| 从最初的 ${Math.abs(s.vi*1e3).toFixed(0)} mV 回落，净充放电电流随之减小。时间常数 τ = ${tau} ns。`);
    }else{
      text('phase','接近新的电流平衡');
      text('observation',`输出趋向 ${target} mV（增益 ${p.gain.toFixed(3)}）。${mode.value==='ideal'?'理想情形下，vgs 的增量最终趋于零。':p.GL>0?'负载分走增量电流，输出停在比开路更低的位置。':'体效应与有限输出电导留下跟随误差；电容决定过程快慢。'}`);
    }
    fields['circuit-description'].textContent=`${active?'阶跃后 '+(t*1e9).toFixed(1)+' 纳秒':'阶跃前'}，输入增量 ${signed(s.vi*1e3)} 毫伏，输出增量 ${signed(s.vo*1e3)} 毫伏，注入源节点的漏电流增量 ${signed(s.id*1e6)} 微安，电容电流 ${signed(s.ic*1e6)} 微安。NMOS 体端独立接地。`;
    fields['response-description'].textContent=`固定零至六百纳秒和正负十毫伏坐标。${active?'当前 '+(t*1e9).toFixed(1)+' 纳秒，输出 '+signed(s.vo*1e3)+' 毫伏，稳态目标 '+target+' 毫伏。':'施加阶跃后显示响应。'}`;
  }

  function pause(){cancelAnimationFrame(frame);frame=0;running=false;}
  function tick(now){
    progress=Math.min(1,Math.max(0,(now-started)/duration));
    if(progress===1)running=false;
    render();
    if(running)frame=requestAnimationFrame(tick);else{frame=0;announce();}
  }
  fields.play.addEventListener('click',()=>{
    if(running){pause();render();announce();return;}
    if(!active||progress>=1)progress=0;
    active=true;
    if(reduced.matches){progress=1;render();announce();return;}
    running=true;started=performance.now()-progress*duration;render();frame=requestAnimationFrame(tick);
  });
  seek.addEventListener('input',()=>{pause();active=true;progress=Number(seek.value)/1000;render();announce();});
  function reset(){pause();active=false;progress=0;render();announce();}
  amplitude.addEventListener('input',reset);mode.addEventListener('change',reset);
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&running){pause();render();}});
  function motionPreference(){fields.reduce.hidden=!reduced.matches;if(reduced.matches&&running){pause();progress=1;render();announce();}}
  reduced.addEventListener('change',motionPreference);motionPreference();render();
  root.hidden=false;root.nextElementSibling.hidden=true;
  root.closest('article').classList.add('sf-enhanced');
  if(location.hash==='#sf-step-title')root.scrollIntoView({block:'start'});
}
