// Bounded, per-column interpolation; no synthetic scaling or extrapolation.
export function interpolate(voltage, rows) {
  if(!Number.isFinite(voltage)||voltage<rows[0][0]-1e-12||voltage>rows.at(-1)[0]+1e-12) throw new RangeError('Outside sweep');
  let lo=0,hi=rows.length-1;
  while(hi-lo>1){const mid=(hi+lo)>>1;if(rows[mid][0]<=voltage)lo=mid;else hi=mid;}
  const f=Math.max(0,Math.min(1,(voltage-rows[lo][0])/(rows[hi][0]-rows[lo][0])));
  return rows[lo].map((v,i)=>v+f*(rows[hi][i]-v));
}
