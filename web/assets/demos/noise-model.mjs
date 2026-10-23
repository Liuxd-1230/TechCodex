/** One-sided PSD, V²/Hz. All integrals return V²; UI alone takes square roots. */
export const S0=1e-16, FC=1000;
export function validateRows(rows){
  if(!Array.isArray(rows)||rows.length<2)throw Error('Missing noise samples');
  rows.forEach((r,i)=>{
    if(r.length!==4||!r.every(Number.isFinite)||r[0]<=0||r.slice(1).some(x=>x<0)||r[1]<=0||
      (i&&r[0]<=rows[i-1][0])||Math.abs(r[2]+r[3]-r[1])>r[1]*1e-8)throw Error('Invalid noise PSD');
  });
  return rows;
}
export function sample(rows,f,column=1){
  if(f<rows[0][0]||f>rows.at(-1)[0])throw RangeError('No frequency extrapolation');
  let l=0,r=rows.length-1;
  while(r-l>1){const m=(l+r)>>1;if(rows[m][0]<=f)l=m;else r=m;}
  const a=rows[l],b=rows[r],t=Math.log(f/a[0])/Math.log(b[0]/a[0]);
  return a[column]&&b[column]?a[column]*Math.exp(Math.log(b[column]/a[column])*t):a[column]+(b[column]-a[column])*(f-a[0])/(b[0]-a[0]);
}
export function integrate(rows,lo,hi,column=1){
  if(!(rows[0][0]<=lo&&lo<hi&&hi<=rows.at(-1)[0]))throw RangeError('Select an ordered band within sampled data');
  let sum=0;
  for(let j=0;j<rows.length-1;j++){
    const [x,y]=[rows[j],rows[j+1]],a=Math.max(x[0],lo),b=Math.min(y[0],hi);
    if(b<=a)continue;
    if(!x[column]||!y[column]){sum+=(sample(rows,a,column)+sample(rows,b,column))*(b-a)/2;continue;}
    const p=Math.log(y[column]/x[column])/Math.log(y[0]/x[0]),q=p+1,t=Math.log(b/a),ya=x[column]*(a/x[0])**p;
    sum+=ya*a*(Math.abs(q)<1e-8?t:Math.expm1(q*t)/q);
  }
  return sum;
}
export function analytic(f,kind){return S0*(1+(kind==='flicker'?FC/f:0));}
export function analyticIntegral(lo,hi,kind){
  if(!(0<lo&&lo<hi))throw RangeError('Ordered positive band required');
  return S0*((hi-lo)+(kind==='flicker'?FC*Math.log(hi/lo):0));
}
export function budget(kind,rows,lo,hi){
  const total=kind==='gf'?integrate(rows,lo,hi):analyticIntegral(lo,hi,kind);
  const flicker=kind==='gf'?integrate(rows,lo,hi,3):kind==='flicker'?S0*FC*Math.log(hi/lo):0;
  return {total,flicker,nonflicker:total-flicker};
}
