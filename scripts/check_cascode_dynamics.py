"""Chapter 6.4: terminal stamps, modal response, native SPICE and archived GF180."""
import json
from pathlib import Path
import numpy as np
from check_frequency import stamp_network
from run import run_deck
from run_frequency import characterize
from bootstrap import verify_models

ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'模拟/实验/频率响应'
BASE=dict(gm1=1e-3,gm2=1e-3,gmb2=.2e-3,g1=1e-5,g2=1e-5,
          rs=1e4,rd=4e4,cgs=1e-12,cf=.1e-12,cx=.5e-12,co=1e-12)


def matrices(p):
    gi=1/p['rs'];gd=1/p['rd'];k=p['gm2']+p['gmb2']+p['g2']
    g=np.array([[gi,0,0],[p['gm1'],p['g1']+k,-p['g2']],[0,-k,gd+p['g2']]])
    c=np.array([[p['cgs']+p['cf'],-p['cf'],0],[-p['cf'],p['cx']+p['cf'],0],[0,0,p['co']]])
    return g,c,np.array([gi,0,0])


def stamped(f,p,fixed=None):
    s=2j*np.pi*f
    devices=[('x','g','0','0',p['gm1'],0,p['g1']),
             ('o','0','x','0',p['gm2'],p['gmb2'],p['g2'])]
    branches=[('g','in',1/p['rs']),('o','0',1/p['rd']),('g','0',s*p['cgs']),
              ('g','x',s*p['cf']),('x','0',s*p['cx']),('o','0',s*p['co'])]
    fixed={'0':0,'in':1,**(fixed or {})}
    nodes=[n for n in ('g','x','o') if n not in fixed]
    return dict(zip(nodes,stamp_network(nodes,devices,branches,fixed)))|fixed


def transfer(f,p):
    s=2j*np.pi*np.asarray(f);gi=1/p['rs'];gd=1/p['rd']
    k=p['gm2']+p['gmb2']+p['g2'];a=gi+s*(p['cgs']+p['cf'])
    b=p['g1']+k+s*(p['cx']+p['cf']);d=gd+p['g2']+s*p['co']
    drive=p['gm1']-s*p['cf'];det=a*(b*d-p['g2']*k)+s*p['cf']*drive*d
    return np.stack([gi*(b*d-p['g2']*k)/det,-gi*drive*d/det,-gi*k*drive/det],axis=-1)


def modes(p):
    g,c,b=matrices(p)
    eigenvalues,v=np.linalg.eig(-np.linalg.solve(c,g))
    residues=v[2,:]*(np.linalg.solve(v,np.linalg.solve(c,b)))
    assert np.all(eigenvalues.real<0)
    return eigenvalues,residues


def bandwidth(p):
    f=np.geomspace(1,1e12,7000);h=transfer(f,p)[:,2]
    return characterize(np.column_stack([f,h.real,h.imag]))['bandwidth_3dB_Hz']


def equations():
    rng=np.random.default_rng(640)
    for _ in range(100):
        p=dict(BASE,gm1=10**rng.uniform(-4,-2),gm2=10**rng.uniform(-4,-2),
               gmb2=10**rng.uniform(-5,-3),g1=10**rng.uniform(-7,-4),g2=10**rng.uniform(-7,-4),
               rd=10**rng.uniform(3,7),rs=10**rng.uniform(2,7))
        k=p['gm2']+p['gmb2']+p['g2'];gi=1/p['rs'];gd=1/p['rd']
        gx=p['g1']+k*gd/(gd+p['g2'])
        dc=stamped(0,p)
        assert np.isclose(dc['x'],-p['gm1']/gx,rtol=1e-10)
        assert np.isclose(dc['o'],dc['x']*k/(gd+p['g2']),rtol=1e-10)
        # Clamp the output at 1 V, not the original loaded amplifier experiment.
        test=stamped(0,p,{'in':0,'o':1})
        assert np.isclose(test['x'],p['g2']/(p['g1']+k),rtol=1e-10)
        for f in (1e3,1e6,1e9):
            s=2j*np.pi*f;g,c,b=matrices(p)
            direct=np.linalg.solve(g+s*c,b);device=stamped(f,p)
            assert np.allclose(direct,[device[n] for n in ('g','x','o')],rtol=1e-9,atol=1e-13)
            assert np.allclose(direct,transfer(f,p),rtol=1e-9,atol=1e-13)
            ev,res=modes(p)
            assert np.isclose(np.sum(res/(s-ev)),direct[2],rtol=1e-8,atol=1e-12)
            # X impedance with gate clamped but its capacitor retained.
            yx=p['g1']+k+s*(p['cx']+p['cf'])-p['g2']*k/(gd+p['g2']+s*p['co'])
            assert np.isclose(device['x']/device['g'],(s*p['cf']-p['gm1'])/yx,rtol=1e-9)
            # Fix the source at 1 V; only M2 conduction receives this test current.
            source_test=stamped(f,p,{'g':0,'x':1})
            upper_current=k-p['g2']*source_test['o']
            zin=(1+p['g2']/(gd+s*p['co']))/k
            assert np.isclose(1/upper_current,zin,rtol=1e-8)
        for rd in (1e-3,1e4,1e9):
            q=dict(p,rd=rd);gdq=1/rd
            assert np.isclose(stamped(0,q)['x'],-p['gm1']/(p['g1']+k*gdq/(gdq+p['g2'])),rtol=1e-8)
    p=dict(BASE,g1=1e-9,g2=1e-9,rd=1e3)
    assert np.isclose(stamped(0,p)['x'],-p['gm1']/(p['gm2']+p['gmb2']),rtol=3e-6)
    # No ro2 feedback, no Cgd1: three independent factors, no RHP zero.
    p=dict(BASE,g2=0,cf=0);k=p['gm2']+p['gmb2']
    for f in (0,1e5,1e8):
        s=2j*np.pi*f
        factor=-p['gm1']*k/((1+s*p['rs']*p['cgs'])*(p['g1']+k+s*p['cx'])*(1/p['rd']+s*p['co']))
        assert np.isclose(stamped(f,p)['o'],factor,rtol=1e-10)
        assert abs(stamped(f,p,{'in':0,'o':1})['x'])<1e-15
    # An ideal gate voltage source removes the gate mode; the bridge remains at X.
    p=dict(BASE);k=p['gm2']+p['gmb2']+p['g2']
    for f in (1e3,1e7,1e10):
        s=2j*np.pi*f;d=1/p['rd']+p['g2']+s*p['co']
        expected=-k*(p['gm1']-s*p['cf'])/((p['g1']+k+s*(p['cx']+p['cf']))*d-p['g2']*k)
        assert np.isclose(stamped(f,p,{'g':1})['o'],expected,rtol=1e-10)
    # Remove Cgd1 and output loading: port impedance has a different test condition.
    p=dict(BASE,cf=0);k=p['gm2']+p['gmb2']+p['g2']
    for f in (1,1e5,1e9):
        s=2j*np.pi*f
        vx=stamped(f,p,{'g':0,'o':1})['x']
        iz=p['g2']-k*vx
        zout=1/p['g2']+(k/p['g2'])/(p['g1']+s*p['cx'])
        assert np.isclose(1/iz,zout,rtol=1e-9)
    # Current-source load, small output conductances: the fast mode is still k/Cx.
    p=dict(BASE,g1=1e-9,g2=1e-8,cf=0)
    k=p['gm2']+p['gmb2']+p['g2']
    gx=np.array([[p['g1']+k,-p['g2']],[-k,p['g2']]])
    cx=np.diag([p['cx'],p['co']])
    eig=np.linalg.eigvals(-np.linalg.solve(cx,gx))
    assert np.all(eig.real<0)
    assert np.isclose(max(abs(eig)),(p['gm2']+p['gmb2'])/p['cx'],rtol=2e-5)
    # The Cf feedforward zero is on positive real s, not a stable natural mode.
    s=BASE['gm1']/BASE['cf'];g,c,b=matrices(BASE)
    assert abs(np.linalg.solve(g+s*c,b)[2])<1e-14
    print('PASS: 100 parameter/termination sets, independent terminal stamps, modal residues, port limits and feedforward zero.')


def native():
    deck=(LAB/'decks/analytic-cascode.cir').read_text(encoding='utf-8')
    maximum=0
    for name,p,changes in [
        ('base',BASE,{}),('cx',dict(BASE,cx=5e-12),{'Cx x 0 .5p':'Cx x 0 5p'}),
        ('rs',dict(BASE,rs=1e6),{'Rsig in g 10k':'Rsig in g 1meg'}),
        ('co',dict(BASE,co=.05e-12),{'Co o 0 1p':'Co o 0 .05p'}),
        ('ideal-ro2',dict(BASE,g2=1e-30),{'Ro2 o x 100k':'Ro2 o x 1e30'}),
        ('output-test',BASE,{'Vin in 0 ac 1':'Vin in 0 ac 0\nVtest o 0 ac 1'})]:
        source=deck
        for before,after in changes.items():
            assert before in source
            source=source.replace(before,after)
        a,=run_deck('ch06/analytic-cascode-'+name,source,['ac.txt'])
        h=a[:,1::2]+1j*a[:,2::2]
        expected=np.array([[stamped(f,p,{'in':0,'o':1})[n] for n in ('g','x','o')] for f in a[:,0]]) if name=='output-test' else transfer(a[:,0],p)
        err=float(np.max(abs(h-expected)/np.maximum(abs(expected),1e-15)))
        assert err<1e-7,(name,err)
        maximum=max(maximum,err)
    print(f'PASS: native ngspice, 6 linear experiments; maximum complex-node relative error {maximum:.3g}.')


def gf180():
    verify_models()
    metrics=json.loads((LAB/'data/metrics.json').read_text(encoding='utf-8'))
    for name in ('cs','cascode','cs-input-limited','cascode-input-limited'):
        deck=(LAB/'decks'/f'{name}.cir').read_text(encoding='utf-8')
        op,ac=run_deck('ch06/recheck-64-'+name,deck,['op.txt','ac.txt'])
        archived=np.loadtxt(LAB/'data'/f'{name}-ac.csv',delimiter=',',skiprows=1)
        assert np.allclose(ac,archived,rtol=2e-6,atol=1e-12)
        assert np.isclose(characterize(ac)['bandwidth_3dB_Hz'],metrics[name]['bandwidth_3dB_Hz'],rtol=1e-6)
        if name.startswith('cascode'):
            q=op[0];margins=[q[6]-q[5],q[1]-q[6]-q[7]]
            assert min(margins)>0
            assert np.allclose(margins,[.4566214567508,.80149327133],atol=1e-9)
    print('PASS: 4 archived GF180 decks reproduced; original complex AC and both saturation margins preserved.')


def main():
    equations();native();gf180()
    previous=np.inf
    for cx in (.05e-12,.5e-12,5e-12):
        p=dict(BASE,cx=cx);ev,_=modes(p)
        assert bandwidth(p)<previous
        previous=bandwidth(p)
        print(f'Cx={cx*1e12:g} pF: pole magnitudes MHz={np.sort(abs(ev))/(2*np.pi*1e6)}, f3dB={bandwidth(p)/1e6:.6f} MHz')
    for key,values in [('rs',(1e3,1e4,1e6)),('co',(.05e-12,1e-12,5e-12))]:
        widths=[bandwidth(dict(BASE,**{key:v})) for v in values]
        assert np.all(np.diff(widths)<0)
        print(key,list(zip(values,np.array(widths)/1e6)))
    for cx,expected_pole,expected_bw in [(.5e-12,67.7092,56.1198),(5e-12,23.7881,22.4861),(50e-12,2.74406,2.74146)]:
        p=dict(BASE,rs=1e3,co=.05e-12,cx=cx);ev,_=modes(p)
        assert np.max(abs(ev.imag))<1e-6
        assert np.isclose(min(abs(ev))/(2*np.pi*1e6),expected_pole,rtol=3e-6)
        assert np.isclose(bandwidth(p)/1e6,expected_bw,rtol=3e-6)
    print('PASS: separate Rs/Co sensitivities and all three textbook Cx examples.')


if __name__=='__main__':main()
