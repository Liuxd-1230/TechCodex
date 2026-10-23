"""Native GF180 frequency experiments. No alteration of Chapter 5 archives."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import numpy as np
from bootstrap import ROOT, simulator, verify_models
from run import common, run_deck
from run_mirrors import mos, control
from frequency_model import PARAMS, response, poles

LAB=ROOT/'模拟/实验/频率响应'; DATA=LAB/'data'
SPEC=json.loads((LAB/'design.json').read_text(encoding='utf-8'))
PREVIOUS=ROOT/'模拟/实验/电流镜/data/metrics.json'
Q=json.loads(PREVIOUS.read_text(encoding='utf-8'))


def write_json(path, obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')


def execute(name, deck, outputs):
    deck='\n'.join(x.rstrip() for x in deck.splitlines())+'\n'
    arrays=run_deck('ch06/'+name,deck,outputs)
    for sub,file,ext in [('decks','run.cir','.cir'),('logs','ngspice.log','.txt')]:
        (LAB/sub).mkdir(parents=True,exist_ok=True)
        src=ROOT/'build/ch06'/name/file
        (LAB/sub/(name+ext)).write_text(src.read_text(encoding='utf-8').rstrip()+'\n',encoding='utf-8',newline='\n')
    for output,a in zip(outputs,arrays):
        name_out=name+'-'+Path(output).stem
        # Complex wrdata preserves real/imaginary parts; no dB/degree ambiguity.
        columns=(ROOT/'build/ch06'/name/output).read_text().splitlines()[0].split()
        assert len(columns)==a.shape[1]
        if output in ('ac.txt','y.txt'):
            columns=['frequency_Hz']+[f'{column}_{"real" if i%2==0 else "imag"}' for i,column in enumerate(columns[1:])]
        else:columns[0]='scale'
        with (DATA/(name_out+'.csv')).open('w',encoding='ascii',newline='\n') as stream:
            np.savetxt(stream,a,delimiter=',',header=','.join(columns),comments='',fmt='%.12e')
    return arrays


def acbody(nodes='v(o)', op='v(o)'):
    return f'op\nwrdata op.txt {op}\nac dec 80 1 10G\nwrdata ac.txt {nodes}'


def ota_base(width=10, clamp=False, stiff=False, length=1, current_scale=1):
    base='Ch06 original Chapter 5 OTA\n'+common()+'.options reltol=1e-9 abstol=1e-16 vntol=1e-12\n'
    base+='Vdd vdd 0 3.3\n'+f'Rref vdd b {Q["reference_resistor_ohm"]/current_scale:.12g}\n'+mos('r','b','b',w=10*current_scale)+mos('t','t','b',w=20*current_scale)
    base+='Vcm cm 0 dc 1.4 ac 0\nVdiff diff 0 dc 0 ac 1\nEp ip cm diff 0 .5\nEn inn cm diff 0 -.5\n'
    base+=mos('1','x','ip','t',w=width*length*current_scale,l=length)+mos('2','o','inn','t',w=width*length*current_scale,l=length)
    base+=mos('3','x','x','vdd','vdd',w=Q['pmos_width_um']*length*current_scale,l=length,p=True)+mos('4','o','x','vdd','vdd',w=Q['pmos_width_um']*length*current_scale,l=length,p=True)
    if stiff:base+=f'Vstiff b 0 dc {Q["ota"]["bias_V"]:.12g} ac 0\n'
    if clamp:
        for n,value in zip(('x','o','t','b'),(Q['ota']['mirror_node_V'],Q['ota']['output_V'],Q['ota']['tail_V'],Q['ota']['bias_V'])):
            base+=f'Vq{n} {n} 0 dc {value:.15g} ac 0\n'
    return base


def crossing(f,y,level):
    candidates=np.flatnonzero((y[:-1]>=level)&(y[1:]<level))
    if not len(candidates):return None
    i=candidates[0]
    return float(np.exp(np.interp(level,[y[i+1],y[i]],[np.log(f[i+1]),np.log(f[i])])) )


def characterize(a):
    h=a[:,1]+1j*a[:,2]; gain=abs(h[0]);db=20*np.log10(abs(h))
    f3=crossing(a[:,0],db,db[0]-10*np.log10(2));fu=crossing(a[:,0],db,0)
    phase=np.unwrap(np.angle(h))*180/np.pi
    return dict(gain_V_V=float(gain),bandwidth_3dB_Hz=f3,unity_Hz=fu,
                phase_at_unity_deg=float(np.interp(np.log(fu),np.log(a[:,0]),phase)) if fu else None)


def matrix_probe():
    """Four accessible-node admittance, measured with AC voltage test sources.
    Internal BSIM nodes are eliminated by native ngspice, not guessed capacitors.
    """
    columns=[];forcing=None
    for active in ('x','o','t','b','input'):
        deck=ota_base(clamp=True)
        body='alter @vdiff[acmag] = 0\n'
        body+=('alter @vdiff[acmag] = 1' if active=='input' else f'alter @vq{active}[acmag] = 1')+'\n'
        body+='ac dec 1 1k 100k\n'
        for n in ('x','o','t','b'):body+=f'let j{n} = -i(Vq{n})\n'
        body+='wrdata y.txt jx jo jt jb'
        a,=execute('probe-'+active,deck+control(body),['y.txt'])
        adm=a[:,1::2]+1j*a[:,2::2]
        if active=='input':forcing=-adm
        else:columns.append(adm)
    y=np.stack(columns,axis=2)
    g=y[0].real;c=y[0].imag/(2*np.pi*a[0,0])
    b0=forcing[0].real;b1=forcing[0].imag/(2*np.pi*a[0,0])
    assert np.allclose(y,y[0].real[None]+2j*np.pi*a[:,0,None,None]*c[None],rtol=.003,atol=1e-10), 'Internal model dispersion invalidates constant G,C'
    assert np.allclose(forcing,b0[None]+2j*np.pi*a[:,0,None]*b1[None],rtol=.003,atol=1e-10)
    return g,c,b0,b1


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    DATA.mkdir(parents=True,exist_ok=True);model=verify_models()
    assert SPEC['supply_V']==3.3 and SPEC['temperature_C']==27 and SPEC['input_common_V']==1.4
    assert SPEC['target']['load_F']==1e-12 and SPEC['points_per_decade']==80 and SPEC['frequency_Hz']==[1,1e10]
    old=json.loads((DATA/'metrics.json').read_text()) if args.check else None
    results={}
    for label,cl,w,stiff,length,scale in [('ota-unloaded',0,10,False,1,1),('ota-1p',1e-12,10,False,1,1),('ota-5p',5e-12,10,False,1,1),('ota-wide',1e-12,20,False,1,1),('ota-long',1e-12,10,False,2,1),('ota-current',1e-12,10,False,1,2),('ota-stiff-bias',1e-12,10,True,1,1)]:
        deck=ota_base(w,stiff=stiff,length=length,current_scale=scale)+f'Cl o 0 {max(cl,1e-24):.12g}\n'
        params=' '.join('@m.x'+n+'.m0['+p+']' for n in ('1','2','3','4','t') for p in ('gm','gmbs','gds','vdsat'))
        body='save all '+params+'\n'+acbody('v(o) v(x) v(t) v(b)','v(o) v(x) v(t) v(b) i(Vdd) '+params)
        op,a=execute(label,deck+control(body),['op.txt','ac.txt'])
        r=characterize(a);r.update(load_F=cl,input_width_um=w*length*scale,core_length_um=length,current_scale=scale,output_V=float(op[0,1]),tail_V=float(op[0,3]),power_W=float(-3.3*op[0,5]),gm_input_S=float(op[0,6]))
        margins=np.array([op[0,2]-op[0,3],op[0,1]-op[0,3],3.3-op[0,2],3.3-op[0,1],op[0,3]])-op[0,9::4]
        r['saturation_margins_V']=margins.tolist();assert min(margins)>0
        results[label]=r
        if w==10 and length==1 and scale==1:
            assert abs(r['output_V']-Q['ota']['output_V'])<1e-6
            assert np.isclose(r['gain_V_V'],Q['ota']['dm_gain'],rtol=1e-5)
    # Independently reconstruct the accessible-node linear circuit and its modes.
    g,c,b0,b1=matrix_probe()
    matrix={k:v.tolist() for k,v in [('G_S',g),('C_F',c),('input_0_S',b0),('input_1_F',b1)]}
    matrix['node_order']=['x','o','t','b'];matrix['loads']={}
    for label,cl in [('ota-unloaded',0),('ota-1p',1e-12),('ota-5p',5e-12)]:
        a=np.loadtxt(DATA/(label+'-ac.csv'),delimiter=',',skiprows=1); cc=c.copy();cc[1,1]+=cl
        h=np.array([np.linalg.solve(g+2j*np.pi*f*cc,b0+2j*np.pi*f*b1)[1] for f in a[:,0]])
        actual=a[:,1]+1j*a[:,2]; use=a[:,0]<=3e7
        err=float(np.max(abs(h[use]-actual[use])/np.maximum(abs(actual[use]),1e-12)))
        assert err<.02, (label,'QS node reconstruction',err)
        ps,rv=np.linalg.eig(-np.linalg.solve(cc,g));assert np.all(ps.real<0)
        lv=np.linalg.inv(rv);order=np.argsort(abs(ps))
        matrix['loads'][label]={'poles_real_imag_rad_s':[[float(ps[k].real),float(ps[k].imag)] for k in order],'modal_participation_abs_X_O_T_B':[np.abs(rv[:,k]*lv[k,:]).tolist() for k in order],'max_relative_error_below_30MHz':err,'Rout_DC_ohm':float(np.linalg.inv(g)[1,1]),'effective_output_C_from_G_C_F':float((np.linalg.inv(g)@cc)[1,1]/np.linalg.inv(g)[1,1])}
    write_json(DATA/'nodal.json',matrix)
    # Actual GF180 stages: same W/L and terminal bias as Chapter 5 where applicable.
    stagebase='Ch06 independent GF180 stage\n'+common()+'Vdd vdd 0 3.3\n'
    configs={
      'cs': 'Vin in 0 dc .900170154106 ac 1\nRsig in g 10k\nRd vdd o 40k\n'+mos('1','o','g')+'Cl o 0 1p\n',
      'cascode': 'Vin in 0 dc .900170154106 ac 1\nRsig in g 10k\nVb bg 0 1.8\nRd vdd o 40k\n'+mos('1','x','g')+mos('2','o','bg','x')+'Cl o 0 1p\n',
      'sf': 'Vin in 0 dc 1.4 ac 1\nRsig in g 10k\nIb o 0 40u\n'+mos('1','vdd','g','o')+'Cl o 0 1p\n',
      'cg': 'Vin in 0 dc 0 ac 1\nVb g 0 .900170154106\nRd vdd o 40k\n'+mos('1','o','g','in')+'Cl o 0 1p\n',
      'passive-diff': 'Vcm cm 0 1.4\nVdiff diff 0 dc 0 ac 1\nEp ip cm diff 0 .5\nEn inn cm diff 0 -.5\nIt t 0 80u\nRd1 vdd x 40k\nRd2 vdd o 40k\n'+mos('1','x','ip','t')+mos('2','o','inn','t')+'Cl1 x 0 1p\nCl2 o 0 1p\n'
    }
    for name in ('cs','cascode'):
        configs[name+'-input-limited']=configs[name].replace('Rsig in g 10k','Rsig in g 1meg').replace('Cl o 0 1p','Cl o 0 .05p')
    for name,circuit in configs.items():
        extra=' v(x) @m.x2.m0[vdsat]' if name.startswith('cascode') else ' v(t)' if name=='passive-diff' else ''
        op,a=execute(name,stagebase+circuit+control(acbody('v(o) v(g)' if name!='passive-diff' else 'v(o) v(x) v(t)','v(o) @m.x1.m0[gm] @m.x1.m0[gmbs] @m.x1.m0[gds] @m.x1.m0[vdsat]'+extra)),['op.txt','ac.txt'])
        results[name]=characterize(a)
        vo=op[0,1];gm=op[0,2];gmb=op[0,3];go=op[0,4]
        if name.startswith('cs') or name=='cg':assert vo>op[0,5]
        if name=='sf':
            assert 3.3-vo>op[0,5]
            assert np.isclose(a[0,1],gm/(gm+gmb+go),rtol=.001)
        if name.startswith('cascode'):
            assert op[0,6]>op[0,5] and vo-op[0,6]>op[0,7]
        if name=='passive-diff':
            assert vo-op[0,6]>op[0,5]
            # Exact matching preserves the differential tail virtual ground.
            assert np.max(abs(a[:,5]+1j*a[:,6]))<1e-5
        results[name]['operating_point_values']=op[0].tolist()
    # Transparent idealized control: Cgd can be removed here, never from BSIM.
    for name,cf in [('analytic-cgd',.1e-12),('analytic-no-cgd',0)]:
        p=dict(PARAMS,cf=cf)
        deck='Ch06 explicit linear CS teaching model\nVin in 0 ac 1\nRsig in g 10k\nRo o 0 50k\nGm o 0 g 0 1m\nCi g 0 1p\nCo o 0 1p\nCf g o '+str(max(cf,1e-30))+'\n'
        a,=execute(name,deck+control('ac dec 80 1 10G\nwrdata ac.txt v(o) v(g)'),['ac.txt'])
        assert np.allclose(a[:,1]+1j*a[:,2],response(a[:,0],**p),rtol=1e-6,atol=1e-8)
        results[name]=dict(characterize(a),poles_rad_s=poles(**p).tolist(),rhp_zero_Hz=PARAMS['gm']/(2*np.pi*cf) if cf else None)
    target=SPEC['target'];r=results['ota-1p']
    results['specification_met']={
        'gain':r['gain_V_V']>=target['minimum_dc_gain_V_V'],
        'bandwidth':r['bandwidth_3dB_Hz']>=target['minimum_3dB_bandwidth_Hz'],
        'power':r['power_W']<=target['maximum_supply_power_W']}
    assert all(results['specification_met'].values()), 'Baseline fails the predeclared nominal target'
    assert results['ota-current']['power_W']>target['maximum_supply_power_W']
    assert results['ota-long']['gain_V_V']>r['gain_V_V'] and results['ota-long']['bandwidth_3dB_Hz']<r['bandwidth_3dB_Hz']
    # Preserve failed choices rather than redefining the goal.
    if old:
        for name in ('ota-1p','ota-5p','cs','sf','cg','cascode'):
            for key in ('gain_V_V','bandwidth_3dB_Hz'):assert np.isclose(results[name][key],old[name][key],rtol=.005)
    write_json(DATA/'metrics.json',results)
    files=[Path(__file__),ROOT/'scripts/frequency_model.py',ROOT/'scripts/check_frequency.py',ROOT/'scripts/run_mirrors.py',ROOT/'scripts/run.py',PREVIOUS,LAB/'design.json']
    files+=sorted((LAB/'decks').glob('*.cir'))+sorted((LAB/'logs').glob('*.txt'))+sorted(DATA.glob('*.csv'))+[DATA/'metrics.json',DATA/'nodal.json']
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    write_json(DATA/'run.json',dict(executed_utc=datetime.now(timezone.utc).isoformat(),platform=platform.system(),python=platform.python_version(),ngspice=subprocess.run([simulator(),'--version'],capture_output=True,text=True,check=True).stdout.strip(),executable_sha256=digest(Path(simulator())),model=model,sha256={p.relative_to(ROOT).as_posix():digest(p) for p in files}))
    print(json.dumps(results,indent=2));print('PASS: native frequency responses, unchanged OTA bias, reconstructed nodal modes, linear-model SPICE cross-check.')


if __name__=='__main__':main()
