import {channel,channelFigure} from './channel-model.mjs';
const root=document.querySelector('[data-demo="mos-channel"]');
if(root){
  const gate=root.querySelector('#channel-gate'),drain=root.querySelector('#channel-drain');
  function render(){
    const vg=+gate.value/100,vd=+drain.value/100,s=channel(vg,vd);
    root.querySelector('#channel-gate-value').textContent=`${vg.toFixed(2)} V`;
    root.querySelector('#channel-drain-value').textContent=`${vd.toFixed(2)} V`;
    gate.setAttribute('aria-valuetext',`${vg.toFixed(2)} 伏`);drain.setAttribute('aria-valuetext',`${vd.toFixed(2)} 伏`);
    root.querySelector('[data-channel="figure"]').innerHTML=channelFigure(vg,vd);
    root.querySelector('[data-channel="result"]').textContent=`${s.saturated?'饱和':'三极区'} · ID = ${(s.id*1e6).toFixed(2)} µA。${s.saturated?'再加漏压，理想电流不变；提高栅压仍会增加源端电荷与饱和电流。':'漏压既推动载流子，也减少漏端电荷；因此输出曲线逐渐弯平。'}`;
  }
  gate.addEventListener('input',render);drain.addEventListener('input',render);render();root.hidden=false;root.closest('article').classList.add('channel-enhanced');
  if(location.hash==='#channel-demo-title')requestAnimationFrame(()=>root.scrollIntoView({block:'start',behavior:'instant'}));
}
