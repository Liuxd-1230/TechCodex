"""One-sided PSD integration, exact for positive power laws between samples."""
import numpy as np


def integrate(f, psd, lo, hi):
    f=np.asarray(f);psd=np.asarray(psd)
    if not (0<f[0]<=lo<hi<=f[-1]) or not np.all(np.diff(f)>0) or not np.all(np.isfinite(psd)) or np.any(psd<0):
        raise ValueError('Finite nonnegative PSD and an in-range ordered band are required')
    total=0.
    for x0,x1,y0,y1 in zip(f[:-1],f[1:],psd[:-1],psd[1:]):
        a=max(x0,lo);b=min(x1,hi)
        if b<=a:continue
        if y0==0 or y1==0:
            ya=y0+(y1-y0)*(a-x0)/(x1-x0);yb=y0+(y1-y0)*(b-x0)/(x1-x0)
            total+=(ya+yb)*(b-a)/2;continue
        p=np.log(y1/y0)/np.log(x1/x0);ya=y0*(a/x0)**p;q=p+1;r=np.log(b/a)
        total+=ya*a*(r if abs(q)<1e-8 else np.expm1(q*r)/q)
    return float(total)
