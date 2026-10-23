/* Constant-parameter two-node CS model. No process data or interpolation. */
export const fixed=Object.freeze({gm:1e-3,rs:1e4,ro:5e4,ci:1e-12,co:1e-12});
const add=(a,b)=>[a[0]+b[0],a[1]+b[1]],mul=(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]];
const div=(a,b)=>{const d=b[0]**2+b[1]**2;return [(a[0]*b[0]+a[1]*b[1])/d,(a[1]*b[0]-a[0]*b[1])/d];};
export const magnitude=z=>Math.hypot(...z);
export const angle=z=>Math.atan2(z[1],z[0])*180/Math.PI;
export function calculate(cf,f,p=fixed){
  if(!Number.isFinite(cf)||cf<0||cf>1.0000001e-12||!Number.isFinite(f)||f<1e4||f>1e10)throw new RangeError('Outside the teaching model controls');
  const {gm,rs,ro,ci,co}=p,gi=1/rs,go=1/ro,w=2*Math.PI*f;
  const d0=gi*go,d1=gi*(co+cf)+go*(ci+cf)+gm*cf,d2=ci*co+cf*(ci+co);
  const fast=(d1+Math.sqrt(d1*d1-4*d0*d2))/(2*d2),slow=d0/(d2*fast);
  const den=[d0-w*w*d2,w*d1],vg=div([gi*go,gi*w*(co+cf)],den),vo=div([-gi*gm,gi*w*cf],den);
  const current=mul([0,w*cf],add(vg,[-vo[0],-vo[1]]));
  const local=div(vo,vg),yin=add([0,w*ci],mul([0,w*cf],[1-local[0],-local[1]]));
  const mi=ci+cf*(1+gm*ro),mo=co+cf*(1+1/(gm*ro));
  const approximate=div([-gm*ro,0],mul([1,w*rs*mi],[1,w*ro*mo]));
  const phase=-(Math.atan(w/slow)+Math.atan(w/fast)+(cf?Math.atan(w*cf/gm):0))*180/Math.PI;
  const approximatePhase=-(Math.atan(w*rs*mi)+Math.atan(w*ro*mo))*180/Math.PI;
  return {vg,vo,current,approximate,phase,approximatePhase,slowHz:slow/(2*Math.PI),fastHz:fast/(2*Math.PI),zeroHz:cf?gm/(2*Math.PI*cf):null,millerInput:mi,storageInput:yin[1]/w,conductanceInput:yin[0]};
}
