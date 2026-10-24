import {modes} from './modes-model.mjs';
const root=document.querySelector('[data-demo="differential-modes"]');
if(root){
  const kind=root.querySelector('#modes-kind'),tail=root.querySelector('#modes-tail'),input=root.querySelector('#modes-input'),get=k=>root.querySelector(`[data-mode="${k}"]`);
  const mv=v=>`${Math.abs(v)<1e-10?'0.00':(v*1e3).toFixed(2)} mV`,ua=i=>`${Math.abs(i)<1e-12?'0.000':(i*1e6).toFixed(3)} µA`;
  function render(){
    const s=modes(kind.value,+input.value/1000,+tail.value);
    get('input-label').textContent=kind.value==='differential'?'差分输入 vid':'共同输入 vic';
    get('input').textContent=mv(+input.value/1000);input.setAttribute('aria-valuetext',get('input').textContent);
    for(const key of ['vi1','vi2','vt','vo1','vo2'])get(key).textContent=`${key} ${mv(s[key])}`;
    for(const key of ['i1','i2','it'])get(key).textContent=`δ${key} ${ua(s[key])}`;
    get('r2').textContent=`RD2 · ${s.r2/1000} kΩ`;get('rt').textContent=Number.isFinite(s.rt)?`rT · ${s.rt/1000} kΩ`:'rT → ∞';
    for(const [key,x,y] of [['i1',115,110],['i2',365,110],['it',205,395]]){
      const i=s[key],dir=i<0?-1:1,len=Math.abs(i)<1e-12?0:12+Math.min(1,Math.abs(i)/1.5e-6)*24;
      get(key+'-arrow').setAttribute('d',len?`M${x} ${y-dir*len/2}V${y+dir*len/2}m-4 ${-dir*7}l4 ${dir*7}l4 ${-dir*7}`:'');
    }
    get('result').textContent=`输出差 vod = ${mv(s.vod)}。`+(kind.value==='differential'?'对称差模下，支路一增一减，尾节点无需改变。':kind.value==='common'?'尾节点移动；两边输出相同，相减仍为零。':'负载不同，共同的电流变化不能换成相同的输出电压。')+` 尾端 KCL：${ua(s.i1)} + ${ua(s.i2)} = ${ua(s.it)}。`;
    root.querySelector('svg desc').textContent=`${get('result').textContent} 尾节点 ${mv(s.vt)}。所有体端接地。`;
  }
  for(const control of [kind,tail,input])control.addEventListener(control===input?'input':'change',render);
  render();root.hidden=false;root.closest('article').classList.add('modes-enhanced');
  if(location.hash==='#modes-demo-title')requestAnimationFrame(()=>root.scrollIntoView({block:'start',behavior:'instant'}));
}
