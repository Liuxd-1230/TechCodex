// Progressive enhancement only; chapters and native details work without this script.
document.querySelectorAll('.md-content figure img').forEach(img => {
  img.decoding = 'async';
});
// Keep the narrow reading area clear while manipulating a circuit.
const demos=document.querySelectorAll('.circuit-demo');
if(demos.length){
  const visible=new Set();
  const observer=new IntersectionObserver(entries=>{
    for(const entry of entries){
      if(entry.isIntersecting)visible.add(entry.target);else visible.delete(entry.target);
    }
    document.body.classList.toggle('book-in-demo',visible.size>0);
  });
  demos.forEach(demo=>observer.observe(demo));
}
const progress=document.querySelector('.book-progress'),article=document.querySelector('article');
if(progress&&article){
  let pending=false;
  function update(){
    pending=false;const top=article.getBoundingClientRect().top+scrollY;
    const extent=Math.max(1,article.getBoundingClientRect().height-innerHeight+80);
    const ratio=Math.max(0,Math.min(1,(scrollY-top+80)/extent));
    progress.firstElementChild.style.transform=`scaleX(${ratio})`;
    progress.setAttribute('aria-valuenow',String(Math.round(ratio*100)));
  }
  function schedule(){if(!pending){pending=true;requestAnimationFrame(update);}}
  progress.hidden=false;addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule);
  new ResizeObserver(schedule).observe(article);update();
}
