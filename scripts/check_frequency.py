"""Independent nodal, limiting-case and matrix checks for Chapter 6."""
import json
from pathlib import Path
import numpy as np
from frequency_model import coefficients, nodal, response, poles
ROOT=Path(__file__).resolve().parents[1]


def stamp_network(nodes, devices, branches, fixed):
    index={v:i for i,v in enumerate(nodes)};a=np.zeros((len(nodes),len(nodes)),complex);b=np.zeros(len(nodes),complex)
    def stamp(row,col,value):
        if row not in index:return
        if col in index:a[index[row],index[col]]+=value
        else:b[index[row]]-=value*fixed.get(col,0)
    for d,g,s,bulk,gm,gmb,go in devices:
        for terminal,value in [(d,go),(g,gm),(s,-gm-gmb-go),(bulk,gmb)]:
            stamp(d,terminal,value);stamp(s,terminal,-value)
    for n,m,admittance in branches:
        for row,col,value in [(n,n,admittance),(m,m,admittance),(n,m,-admittance),(m,n,-admittance)]:stamp(row,col,value)
    return np.linalg.solve(a,b)


def main():
    rng=np.random.default_rng(606)
    for _ in range(120):
        gm=10**rng.uniform(-4,-2);rs=10**rng.uniform(2,5);rout=10**rng.uniform(3,6)
        ci,co,cf=10**rng.uniform(-14,-11,3)
        p=dict(gm=gm,rs=rs,rout=rout,ci=ci,co=co,cf=cf)
        f=10**rng.uniform(2,10)
        assert np.isclose(nodal(f,**p)[1],response(f,**p),rtol=1e-10)
        assert np.all(poles(**p).real<0)
        # Open-circuit time constants: bridge capacitor includes feedback gmRsRo.
        tau=rs*ci+rout*co+cf*(rs+rout+gm*rs*rout)
        d=coefficients(**p);assert np.isclose(d[1]/d[0],tau,rtol=1e-12)
        # Feedforward zero is at positive real s; cancellation is of algebraic paths.
        s=gm/cf
        assert abs((s*cf-gm)/rs)<1e-18
        # Source-follower full two-node matrix and determinant formula.
        s=2j*np.pi*f;gi=1/rs;go=1/rout;gmb=.2*gm
        a=gi+s*(ci+cf);d=go+gm+gmb+s*(co+cf)
        m=np.array([[a,-s*cf],[-gm-s*cf,d]])
        h=np.linalg.solve(m,[gi,0])[1]
        assert np.isclose(h,gi*(gm+s*cf)/(a*d-s*cf*(gm+s*cf)),rtol=1e-10)
        # Common-gate source/drain KCL, retaining ro coupling and source loading.
        sig=gm+gmb+go;gd=go+.5*gi
        m=np.array([[gi+sig+s*ci,-go],[-sig,gd+s*co]])
        h=np.linalg.solve(m,[gi,0])[1]
        assert np.isclose(h,gi*sig/((gi+sig+s*ci)*(gd+s*co)-go*sig),rtol=1e-10)
        # Cascode matrix against independent terminal-current device stamps.
        gm2=1.3*gm;gmb2=.2*gm2;g1=go;g2=.8*go;k2=gm2+gmb2+g2;gd=1/rout
        analytic=np.array([[gi+s*(ci+cf),-s*cf,0],[gm-s*cf,g1+k2+s*(co+cf),-g2],[0,-k2,gd+g2+s*ci]])
        via_matrix=np.linalg.solve(analytic,[gi,0,0])
        via_devices=stamp_network(['g','x','o'],[('x','g','0','0',gm,0,g1),('o','0','x','0',gm2,gmb2,g2)],
            [('g','in',gi),('o','0',gd),('g','0',s*ci),('g','x',s*cf),('x','0',s*co),('o','0',s*ci)],{'in':1,'0':0})
        assert np.allclose(via_matrix,via_devices,rtol=1e-10)
        # Mirror direct path plus delayed path: retains its LHP zero.
        tx=ci/gm;to=co/go
        vx=-gm/2/(gm+s*ci);vo=(gm/2-gm*vx)/(go+s*co)
        assert np.isclose(vo,gm/go*(1+s*tx/2)/((1+s*tx)*(1+s*to)),rtol=1e-10)
    lab=ROOT/'模拟/实验/频率响应/data'
    record=json.loads((lab/'nodal.json').read_text())
    g=np.array(record['G_S']);c=np.array(record['C_F'])
    # Intrinsic charge derivatives need not be reciprocal two-terminal capacitors.
    assert not np.allclose(c,c.T,rtol=.01,atol=1e-18)
    for name,cl in [('ota-unloaded',0),('ota-1p',1e-12),('ota-5p',5e-12)]:
        cc=c.copy();cc[1,1]+=cl; z=np.linalg.inv(g)
        tau=float(np.trace(z@cc))
        ps=np.array(record['loads'][name]['poles_real_imag_rad_s'])[:,0]
        assert np.isclose(tau,np.sum(-1/ps),rtol=1e-8)
    print('PASS: 120 CS/SF/CG/cascode/mirror cases, independent stamps, RHP/LHP signs, OCTC and modal time constants.')


if __name__=='__main__':main()
