// Progressive enhancement only; chapters and native details work without this script.
document.querySelectorAll('.md-content figure img').forEach(img => {
  img.decoding = 'async';
});
// Keep mobile diagrams, captions and controls clear of floating navigation.
const evidence=document.querySelectorAll('.circuit-demo, .md-content figure');
if(evidence.length){
  const visible=new Set();
  const observer=new IntersectionObserver(entries=>{
    for(const entry of entries){
      if(entry.isIntersecting)visible.add(entry.target);else visible.delete(entry.target);
    }
    document.body.classList.toggle('book-in-evidence',visible.size>0);
  });
  evidence.forEach(element=>observer.observe(element));
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
