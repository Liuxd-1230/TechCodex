"""Independent analytic, terminal-current, covariance and archived-data checks."""
import hashlib,json
from pathlib import Path
import numpy as np
from noise_math import integrate
ROOT=Path(__file__).resolve().parents[1]


def network(nodes,devices,resistors,source,fixed=None):
    """Stamp D/S terminal currents, rather than the chapter's reduced formulas."""
    ix={n:i for i,n in enumerate(nodes)};a=np.zeros((len(nodes),len(nodes)));b=np.zeros(len(nodes));fixed=fixed or {}
    def stamp(row,col,v):
        if row not in ix:return
        if col in ix:a[ix[row],ix[col]]+=v
        else:b[ix[row]]-=v*fixed.get(col,0)
    for d,g,s,bulk,gm,gmb,go in devices:
        for n,v in [(d,go),(g,gm),(s,-gm-gmb-go),(bulk,gmb)]:stamp(d,n,v);stamp(s,n,-v)
    for n,m,g in resistors:
        for row,col,v in [(n,n,g),(m,m,g),(n,m,-g),(m,n,-g)]:stamp(row,col,v)
    for n,v in source.items():b[ix[n]]+=v
    return np.linalg.solve(a,b)


def main():
    f=np.geomspace(1,1e7,701);lo,hi=13,234567
    assert np.isclose(integrate(f,np.ones_like(f)*2e-16,lo,hi),2e-16*(hi-lo),rtol=1e-12,atol=0)
    assert np.isclose(integrate(f,3e-13/f,lo,hi),3e-13*np.log(hi/lo),rtol=1e-12,atol=0)
    fp=15915.4943;p=1.6576071894e-16/(1+(f/fp)**2)
    assert np.isclose(integrate(f,p,lo,hi),1.6576071894e-16*fp*(np.arctan(hi/fp)-np.arctan(lo/fp)),rtol=1e-4,atol=0)
    for a,b in [(0,2),(2,2),(10,1e9)]:
        try:integrate(f,p,a,b)
        except ValueError:pass
        else:raise AssertionError('Invalid band accepted')
    rng=np.random.default_rng(707)
    for _ in range(150):
        gm=10**rng.uniform(-4,-2);gmb=.2*gm;g1=gm/rng.uniform(10,100);g2=g1*.8;gd=10**rng.uniform(-6,-3);gs=10**rng.uniform(-5,-2)
        # Common-gate noise injects opposite currents at drain and source.
        d=[('o','0','x','0',gm,gmb,0)];r=[('x','in',gs),('o','0',gd)]
        signal=network(['x','o'],d,r,{}, {'in':1})
        noise=network(['x','o'],d,r,{'x':1,'o':-1})
        assert np.isclose(noise[1]/signal[1],-1/(gm+gmb),rtol=1e-10)
        # Cascode: signal and two noise sources stamped at physical terminals.
        gm2=1.4*gm;k2=gm2+.2*gm2+g2
        d=[('x','in','0','0',gm,0,g1),('o','0','x','0',gm2,.2*gm2,g2)];r=[('o','0',gd)]
        signal=network(['x','o'],d,r,{}, {'in':1})[1]
        lower=network(['x','o'],d,r,{'x':-1})[1];upper=network(['x','o'],d,r,{'x':1,'o':-1})[1]
        assert np.isclose(lower/signal,1/gm,rtol=1e-10)
        assert np.isclose(upper/signal,g1/(gm*k2),rtol=1e-10)
        # Correlated complex spectra remain positive; quadratic form vs paths.
        z=rng.normal(size=(3,3))+1j*rng.normal(size=(3,3));S=z@z.conj().T
        h=rng.normal(size=3)+1j*rng.normal(size=3);power=h@S@h.conj()
        independent=sum(abs(x)**2 for x in h@z)
        assert power.real>=0 and abs(power.imag)<1e-10 and np.isclose(power.real,independent)
    lab=ROOT/'模拟/实验/噪声/data';m=json.loads((lab/'metrics.json').read_text(encoding='utf-8'))
    for name,r in m.items():
        if name=='resistor_calibration':continue
        a=np.loadtxt(lab/(name+'-spectrum.csv'),delimiter=',',skiprows=1)
        for b in r['bands']:
            assert np.isclose(integrate(a[:,0],a[:,2],*b['band_Hz']),b['input_rms_V']**2,rtol=1e-10,atol=0)
            assert np.isclose(sum(b['source_input_variance_V2'].values()),b['input_rms_V']**2,rtol=1e-5,atol=0)
    assert all(m['area-budget']['meets'].values())
    assert not m['baseline']['meets']['noise'] and not m['all-width-current-2x']['meets']['power']
    assert np.isclose(m['baseline']['bands'][1]['input_rms_V'],m['baseline-5p']['bands'][1]['input_rms_V'],rtol=1e-10)
    for name,digest in json.loads((lab/'run.json').read_text(encoding='utf-8'))['sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    print('PASS: one-sided white/1/f/RC integrals; 150 terminal-current CG/cascode and complex covariance cases; all GF source budgets and hashes.')


if __name__=='__main__':main()
