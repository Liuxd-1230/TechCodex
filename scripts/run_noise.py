"""Actual GF180 BSIM .noise, source decomposition and unchanged-baseline checks."""
from datetime import datetime,timezone
import argparse,hashlib,json,platform,subprocess
from pathlib import Path
import numpy as np
from bootstrap import ROOT,simulator,verify_models
from run import run_deck
from run_mirrors import control,mos
from run_frequency import ota_base,characterize,Q
from noise_math import integrate
LAB=ROOT/'模拟/实验/噪声';DATA=LAB/'data'
SPEC=json.loads((LAB/'design.json').read_text(encoding='utf-8'))
DEVICES=('1','2','3','4','t','r')


def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def execute(name,deck,outputs,headers):
    deck='\n'.join(line.rstrip() for line in deck.splitlines())+'\n'
    arrays=run_deck('ch07/'+name,deck,outputs)
    for folder,source,suffix in [('decks','run.cir','.cir'),('logs','ngspice.log','.txt')]:
        (LAB/folder).mkdir(parents=True,exist_ok=True)
        text=(ROOT/'build/ch07'/name/source).read_text(encoding='utf-8').rstrip()+'\n'
        (LAB/folder/(name+suffix)).write_text(text,encoding='utf-8',newline='\n')
    for file,a,header in zip(outputs,arrays,headers):
        assert len(header.split(','))==a.shape[1],(file,a.shape,header)
        with (DATA/(name+'-'+Path(file).stem+'.csv')).open('w',encoding='ascii',newline='\n') as out:
            np.savetxt(out,a,delimiter=',',header=header,comments='',fmt='%.12e')
    return arrays


def large_area_base():
    # The pinned model bins stop at W=100 um. Explicit parallel units also
    # avoid the wrapper's unused m parameter and unsupported total-W binning.
    base=ota_base(width=100)
    for prefix,d,g in [('1','x','ip'),('2','o','inn')]:
        for i in range(1,10):base+=mos(prefix+'p'+str(i),d,g,'t',w=100)
    for n,d in [('3','x'),('4','o')]:
        old=mos(n,d,'x','vdd','vdd',w=Q['pmos_width_um'],p=True)
        assert base.count(old)==1
        base=base.replace(old,mos(n,d,'x','vdd','vdd',w=Q['pmos_width_um']*10,l=10,p=True))
    return base


def ota_noise(name,base,cl=1e-12):
    groups={d:[d] for d in DEVICES}
    if name=='area-budget':
        for d in ('1','2'):groups[d]+=[d+'p'+str(i) for i in range(1,10)]
    params=' '.join('@m.x'+n+'.m0['+p+']' for names in groups.values() for n in names for p in ('gm','gmbs','gds','vdsat'))
    deck=base.replace('Ch06 original chapter 5 OTA','Ch07 actual GF180 noise')+f'Cl o 0 {cl:.12g}\n'
    body='save all '+params+'\nop\n'
    opnames=[]
    for d in ('1','2','3','4','t'):
        for p in ('gm','gmbs','gds','vdsat'):
            label='q'+d+'_'+p;opnames.append(label)
            terms=groups[d][:1] if p=='vdsat' else groups[d]
            body+='let '+label+' = '+' + '.join('@m.x'+n+'.m0['+p+']' for n in terms)+'\n'
    body+='wrdata op.txt v(o) v(x) v(t) v(b) i(Vdd) '+' '.join(opnames)+'\n'
    body+='ac dec 100 1 1G\nwrdata ac.txt v(o)\nset sqrnoise\nnoise v(o) Vdiff dec 100 1 1G 1\nsetplot noise1\n'
    for d in DEVICES:
        for kind in ('','id','1overf'):
            label='n'+d+('_'+kind if kind else '')
            body+='let '+label+' = '+' + '.join('onoise.m.x'+n+'.m0'+('.'+kind if kind else '') for n in groups[d])+'\n'
    vectors=['onoise_spectrum','inoise_spectrum']+['n'+d for d in DEVICES]+['onoise_rref']
    vectors += ['n'+d+'_'+kind for kind in ('id','1overf') for d in DEVICES]
    body+='wrdata spectrum.txt '+' '.join(vectors)+'\nsetplot noise2\nwrdata totals.txt onoise_total inoise_total\n'
    headers=['scale,vo_V,x_V,t_V,b_V,supply_A,'+','.join(n+'_'+p for n in ('1','2','3','4','t') for p in ('gm_S','gmb_S','gds_S','vdsat_V')),
             'frequency_Hz,gain_real_V_V,gain_imag_V_V',
             'frequency_Hz,output_V2_Hz,input_V2_Hz,'+','.join('M'+d+'_output_V2_Hz' for d in DEVICES)+',Rref_output_V2_Hz,'+','.join('M'+d+'_'+kind+'_output_V2_Hz' for kind in ('channel','flicker') for d in DEVICES),
             'scale,output_V2,input_V2']
    op,ac,sp,total=execute(name,deck+control(body),['op.txt','ac.txt','spectrum.txt','totals.txt'],headers)
    gain2=ac[:,1]**2+ac[:,2]**2
    assert np.allclose(sp[:,0],ac[:,0]) and np.all(sp[:,1:3]>0)
    assert np.allclose(sp[:,1]/gain2,sp[:,2],rtol=1e-8), 'Wrong input reference or ASD/PSD convention'
    assert np.allclose(sp[:,3:10].sum(axis=1),sp[:,1],rtol=1e-8,atol=1e-35), 'Available source groups do not sum'
    for column,label in [(1,'output'),(2,'input')]:
        assert np.isclose(integrate(sp[:,0],sp[:,column],sp[0,0],sp[-1,0]),total[0,column],rtol=.003),label
    f=sp[:,0];flicker=sp[:,16:22].sum(axis=1);channel=sp[:,10:16].sum(axis=1)
    other=sp[:,1]-flicker-channel
    assert np.min(other)>-np.max(sp[:,1])*1e-12
    white=sp[:,1]-flicker
    bands=[]
    for lo,hi in SPEC['comparison_bands_Hz']:
        input_ms=integrate(f,sp[:,2],lo,hi);out_ms=integrate(f,sp[:,1],lo,hi)
        group_ms={label:integrate(f,psd/gain2,lo,hi) for label,psd in [('input_pair',sp[:,3]+sp[:,4]),('pmos_mirror',sp[:,5]+sp[:,6]),('tail',sp[:,7]),('reference_MR_R',sp[:,8]+sp[:,9])]}
        bands.append(dict(band_Hz=[lo,hi],input_rms_V=float(np.sqrt(input_ms)),output_rms_V=float(np.sqrt(out_ms)),output_rms_over_DC_gain_V=float(np.sqrt(out_ms/gain2[0])),source_input_variance_V2=group_ms,flicker_fraction=integrate(f,flicker/gain2,lo,hi)/input_ms))
    p=op[0];margins=np.array([p[2]-p[3],p[1]-p[3],3.3-p[2],3.3-p[1],p[3]])-p[9::4]
    assert np.min(margins)>0
    r=characterize(ac);r.update(output_V=float(p[1]),tail_V=float(p[3]),power_W=float(-3.3*p[5]),gm_input_S=float(p[6]),saturation_margins_V=margins.tolist(),load_F=cl,bands=bands)
    target=SPEC['target'];main=bands[1]
    r['meets']={key:bool(value) for key,value in dict(noise=main['input_rms_V']<=target['maximum_input_referred_rms_V'],gain=r['gain_V_V']>=target['minimum_dc_gain_V_V'],bandwidth=r['bandwidth_3dB_Hz']>=target['minimum_3dB_bandwidth_Hz'],power=r['power_W']<=target['maximum_supply_power_W']).items()}
    r['snr_for_100uV_dB']=float(20*np.log10(target['input_signal_rms_V']/main['input_rms_V']))
    ratio=flicker/np.maximum(white,1e-300);idx=np.flatnonzero((ratio[:-1]>=1)&(ratio[1:]<1))
    r['output_mechanism_crossover_Hz']=float(np.exp(np.interp(0,np.log(ratio[idx[0]:idx[0]+2])[::-1],np.log(f[idx[0]:idx[0]+2])[::-1]))) if len(idx) else None
    return r


def resistor_check():
    deck='Ch07 calibrate one-sided PSD with an ideal resistor\n.temp 27\nVin in 0 dc 0 ac 1\nR1 in o 10k\nC1 o 0 1n\n'
    body='set sqrnoise\nnoise v(o) Vin dec 100 1 1meg\nsetplot noise1\nwrdata spectrum.txt onoise_spectrum inoise_spectrum\nsetplot noise2\nwrdata total.txt onoise_total inoise_total'
    sp,t=execute('resistor',deck+control(body),['spectrum.txt','total.txt'],['frequency_Hz,output_V2_Hz,input_V2_Hz','scale,output_V2,input_V2'])
    k=1.380649e-23;level=4*k*300.15*1e4;fp=1/(2*np.pi*1e4*1e-9)
    assert np.allclose(sp[:,2],level,rtol=1e-6)
    assert np.allclose(sp[:,1],level/(1+(sp[:,0]/fp)**2),rtol=1e-6)
    exact=level*fp*(np.arctan(sp[-1,0]/fp)-np.arctan(sp[0,0]/fp))
    assert np.isclose(t[0,1],exact,rtol=.001)
    return dict(input_psd_V2_Hz=level,output_variance_V2=float(t[0,1]),analytic_variance_V2=float(exact),pole_Hz=fp)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    DATA.mkdir(parents=True,exist_ok=True);model=verify_models()
    old=json.loads((DATA/'metrics.json').read_text()) if args.check else None
    cases=[('baseline',ota_base(),1e-12),('input-width-2x',ota_base(width=20),1e-12),('all-width-current-2x',ota_base(current_scale=2),1e-12),('baseline-5p',ota_base(),5e-12),('area-budget',large_area_base(),1e-12)]
    results={n:ota_noise(n,b,c) for n,b,c in cases}
    for name in ('baseline','baseline-5p'):
        assert np.isclose(results[name]['gain_V_V'],Q['ota']['dm_gain'],rtol=1e-5)
        assert np.isclose(results[name]['output_V'],Q['ota']['output_V'],atol=1e-6)
    if old:
        for name in results:
            if name in old:
                assert np.isclose(results[name]['bands'][1]['input_rms_V'],old[name]['bands'][1]['input_rms_V'],rtol=.005)
    results['resistor_calibration']=resistor_check();dump(DATA/'metrics.json',results)
    paths=[Path(__file__),ROOT/'scripts/noise_math.py',ROOT/'scripts/run_frequency.py',ROOT/'scripts/run_mirrors.py',ROOT/'scripts/run.py',ROOT/'模拟/实验/电流镜/data/metrics.json',LAB/'design.json']
    if (LAB/'adjustment.json').exists():paths.append(LAB/'adjustment.json')
    paths+=sorted((LAB/'decks').glob('*.cir'))+sorted((LAB/'logs').glob('*.txt'))+sorted(DATA.glob('*.csv'))+[DATA/'metrics.json']
    paths+=sorted(p for p in (LAB/'compatibility').rglob('*') if p.is_file())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    dump(DATA/'run.json',dict(executed_utc=datetime.now(timezone.utc).isoformat(),platform=platform.system(),ngspice=subprocess.run([simulator(),'--version'],capture_output=True,text=True,check=True).stdout.strip(),executable_sha256=digest(Path(simulator())),model=model,settings=dict(one_sided=True,sqrnoise=True,fnoimod=1,tnoimod=0,solver='SPARSE 1.3',junction_AD_AS_m2=5e-12,junction_PD_PS_m=21e-6),sha256={p.relative_to(ROOT).as_posix():digest(p) for p in paths}))
    for name in [n for n,_,_ in cases]:
        r=results[name];print(name,dict(input_uV=r['bands'][1]['input_rms_V']*1e6,gain=r['gain_V_V'],bandwidth_Hz=r['bandwidth_3dB_Hz'],power_mW=r['power_W']*1e3,meets=r['meets'],flicker_fraction=r['bands'][1]['flicker_fraction'],sources=r['bands'][1]['source_input_variance_V2']))
    print('PASS: genuine .noise, one-sided resistor calibration, gain reference, source sums, independent PSD integrations and DC/work-region checks.')


if __name__=='__main__':main()
