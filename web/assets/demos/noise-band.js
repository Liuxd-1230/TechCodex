import {validateRows,sample,analytic,budget} from './noise-model.mjs';
const root=document.querySelector('[data-demo="noise-band"]');
async function start(){
  const response=await fetch(root.dataset.payload);
  if(!response.ok)throw Error('Noise data unavailable');
  const payload=await response.json();
  if(payload.schema!==1)throw Error('Unsupported noise data');
  const rows=validateRows(payload.rows),get=k=>root.querySelector(`[data-noise="${k}"]`);
  const low=root.querySelector('#noise-low'),high=root.querySelector('#noise-high'),source=root.querySelector('#noise-source');
  const reduce=matchMedia('(prefers-reduced-motion: reduce)');
  let kind=source.value,current=[+low.value,+high.value],target=[...current],from=[...current],began=0,frame=0,announce;
  const frequencies=Array.from({length:241},(_,i)=>10**(i/40));
  let logMin,logMax,yMax;
  const x=f=>65+Math.log10(f)*87.5,yASD=p=>170-(Math.log10(Math.sqrt(p)*1e9)-logMin)/(logMax-logMin)*125;
  const yVariance=(f,p)=>345-Math.LN10*f*p*1e12/yMax*125;
  const psd=f=>kind==='gf'?sample(rows,f):analytic(f,kind);
  const hz=f=>f>=1e6?'1 MHz':f>=1e3?`${+(f/1000).toPrecision(3)} kHz`:`${+f.toPrecision(3)} Hz`;
  const path=points=>points.map(([a,b],i)=>`${i?'L':'M'}${a.toFixed(2)} ${b.toFixed(2)}`).join('');
  function spectra(){
    const levels=frequencies.map(f=>Math.sqrt(psd(f))*1e9);
    logMin=Math.floor(Math.log10(Math.min(...levels)))-.1;logMax=Math.ceil(Math.log10(Math.max(...levels)))+.1;
    yMax=Math.max(...frequencies.map(f=>Math.LN10*f*psd(f)*1e12))*1.08;
    get('asd').setAttribute('d',path(frequencies.map(f=>[x(f),yASD(psd(f))])));
    get('density').setAttribute('d',path(frequencies.map(f=>[x(f),yVariance(f,psd(f))])));
    let grid='',ticks='<text x="65" y="24">ASD / nV·Hz⁻½</text><text x="65" y="205">方差 / µV²·decade⁻¹</text>';
    for(let i=0;i<=6;i++){
      const X=x(10**i);grid+=`<path d="M${X} 45V170M${X} 220V345"/>`;
      ticks+=`<text x="${X}" y="373" text-anchor="middle">${['1','10','100','1k','10k','100k','1M'][i]}</text>`;
    }
    for(let i=Math.ceil(logMin);i<logMax;i++){
      const Y=yASD((10**i/1e9)**2);grid+=`<path d="M65 ${Y}H590"/>`;
      ticks+=`<text x="55" y="${Y+6}" text-anchor="end">${i>=3?(10**i/1000)+'k':10**i}</text>`;
    }
    for(let i=0;i<=2;i++){
      const Y=345-i*62.5;grid+=`<path d="M65 ${Y}H590"/>`;
      ticks+=`<text x="55" y="${Y+6}" text-anchor="end">${+(yMax*i/2).toPrecision(3)}</text>`;
    }
    ticks+='<text x="328" y="402" text-anchor="middle">频率 / Hz · 对数坐标</text>';
    get('grid').innerHTML=grid;get('ticks').innerHTML=ticks;
    get('source').textContent=kind==='gf'?'预计算 GF180 · 固定原 OTA、27 °C、1 pF；此处没有实时 SPICE。':`实时解析模型 · 10 nV/√Hz 白噪声${kind==='flicker'?' + fc=1 kHz 的 1/f 项':''}。`;
  }
  function render(){
    const [lo,hi]=current.map(v=>10**(v/100)),b=budget(kind,rows,lo,hi);
    get('low').textContent=hz(lo);get('high').textContent=hz(hi);
    get('rms').textContent=`${(Math.sqrt(b.total)*1e6).toFixed(2)} µV RMS`;
    const fraction=b.flicker/b.total;
    get('fraction').textContent=`闪烁方差 ${(fraction*100).toFixed(1)}% · ${kind==='gf'?'非闪烁':'白噪声'}方差 ${((1-fraction)*100).toFixed(1)}%`;
    const a=x(lo),z=x(hi);
    get('band').setAttribute('d',`M${a} 45H${z}V170H${a}ZM${a} 220H${z}V345H${a}Z`);
    get('edges').setAttribute('d',`M${a} 45V170M${z} 45V170M${a} 220V345M${z} 220V345`);
    const selected=[lo,...frequencies.filter(f=>f>lo&&f<hi),hi];
    get('area').setAttribute('d',path([[a,345],...selected.map(f=>[x(f),yVariance(f,psd(f))]),[z,345]])+'Z');
    get('observation').textContent=kind==='white'?'每一赫兹分到相同方差。下图向高频上升，是因为高频的每个十倍频程包含更多赫兹。带宽扩大十倍时，RMS 约扩大 √10 倍。':fraction>.7?'这段频带主要由闪烁项贡献。观察下图低频部分：每个十倍频程的方差近似相同；降低下限会不断累加低频噪声。':'这段频带中非闪烁项已不可忽略。继续提高上限，会纳入越来越多的宽带噪声；降低低频噪声不能代替带宽预算。';
  }
  function speak(){clearTimeout(announce);announce=setTimeout(()=>{get('announcement').textContent=`${get('low').textContent} 到 ${get('high').textContent}，${get('rms').textContent}。${get('fraction').textContent}`;},220);}
  function tick(now){
    const u=Math.min(1,(now-began)/180),ease=1-(1-u)**3;
    // Floating-point easing can overshoot 600 by an ulp at the final frame.
    // Keep the visible band inside the sampled 1 Hz–1 MHz domain at all times.
    current=u===1?[...target]:from.map((v,i)=>Math.max(0,Math.min(600,v+(target[i]-v)*ease)));render();
    if(u<1)frame=requestAnimationFrame(tick);else frame=0;
  }
  function update(){
    cancelAnimationFrame(frame);frame=0;target=[+low.value,+high.value];
    // Accessible values track the current target, while all chart/readout values
    // share the animated band at every frame. A new input interrupts this tween.
    low.setAttribute('aria-valuetext',hz(10**(target[0]/100)));high.setAttribute('aria-valuetext',hz(10**(target[1]/100)));
    if(reduce.matches||document.hidden){current=[...target];render();}
    else{from=[...current];began=performance.now();frame=requestAnimationFrame(tick);}
    speak();
  }
  low.addEventListener('input',()=>{if(+low.value>=+high.value)low.value=+high.value-5;update();});
  high.addEventListener('input',()=>{if(+high.value<=+low.value)high.value=+low.value+5;update();});
  source.addEventListener('change',()=>{cancelAnimationFrame(frame);frame=0;current=[+low.value,+high.value];kind=source.value;spectra();render();speak();});
  function settle(){if(frame){cancelAnimationFrame(frame);frame=0;current=[...target];render();}}
  reduce.addEventListener('change',()=>{if(reduce.matches)settle();});document.addEventListener('visibilitychange',()=>{if(document.hidden)settle();});
  spectra();render();root.hidden=false;
  low.setAttribute('aria-valuetext',hz(100));high.setAttribute('aria-valuetext',hz(1e5));
  if(location.hash==='#noise-demo-title')requestAnimationFrame(()=>root.scrollIntoView({block:'start',behavior:'instant'}));
}
if(root)start().catch(()=>{const fallback=root.nextElementSibling;if(fallback?.classList.contains('demo-loading'))fallback.hidden=false;});
