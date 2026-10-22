"""Chapter 5: design-first mirrors and a resistor-referenced five-transistor OTA core."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path
import numpy as np
from bootstrap import ROOT, simulator, verify_models
from run import common, run_deck
from check_teaching import solve

LAB = ROOT/'模拟/实验/电流镜'
DATA = LAB/'data'
SPEC = json.loads((LAB/'design.json').read_text(encoding='utf-8'))


def csv(name, header, array):
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA/(name+'.csv')).open('w', encoding='ascii', newline='\n') as stream:
        np.savetxt(stream, array, delimiter=',', header=header, comments='', fmt='%.12e')


def execute(name, source, expected):
    source = '\n'.join(line.rstrip() for line in source.splitlines())+'\n'
    arrays = run_deck('ch05/'+name, source, expected)
    for folder, filename in [('decks','run.cir'), ('logs','ngspice.log')]:
        (LAB/folder).mkdir(parents=True, exist_ok=True)
        destination=LAB/folder/(name+('.cir' if folder=='decks' else '.txt'))
        original=ROOT/'build/ch05'/name/filename
        if folder=='logs':
            destination.write_text(original.read_text(encoding='utf-8').rstrip()+'\n',encoding='utf-8',newline='\n')
        else:shutil.copyfile(original,destination)
    return arrays


def mos(name, d, g, s='0', bulk='0', w=10, l=1, p=False):
    # Fixed junction geometry, explicitly recorded. Not a layout extraction.
    return f'X{name} {d} {g} {s} {bulk} {"p" if p else "n"}mos_3p3 w={w:.12g}u l={l:.12g}u ad=5p as=5p pd=21u ps=21u\n'


def control(body):
    return '.control\nset noaskquit\nset wr_singlescale\nset wr_vecnames\nset numdgt=15\n'+body+'\nquit\n.endc\n.end\n'


def mirror(name, w, l, cascode=False, corner='typical', temp=27):
    base = 'Ch05 mirror\n'+common(corner,temp)+'.options reltol=1e-9 abstol=1e-16 vntol=1e-12\nVdd vdd 0 3.3\nVout o 0 1.65\n'
    base += 'Iref vdd '+('bc' if cascode else 'b')+' 40u\n'+mos('1','b','b',w=w,l=l)
    if cascode:
        base += mos('3','bc','bc','b',w=w,l=l)+mos('2','x','b',w=w,l=l)+mos('4','o','bc','x',w=w,l=l)
        bottom, upper = 'v(x)', '@m.x4.m0[vdsat]'
    else:
        base += mos('2','o','b',w=w,l=l)
        bottom, upper = 'v(o)', 'v(o)*0'
    body = ('save all @m.x2.m0[vdsat] '+('@m.x4.m0[vdsat]' if cascode else '')+'\n'
            'dc Vout .05 3.0 .01\nlet io = -i(Vout)\n'
            f'wrdata sweep.txt io v(b) {bottom} @m.x2.m0[vdsat] {upper}\n')
    a, = execute(name, base+control(body), ['sweep.txt'])
    csv(name, 'output_V,current_A,gate_V,internal_V,bottom_vdsat_V,upper_vdsat_V', a)
    valid = (a[:,3] >= a[:,4]) & ((a[:,0]-a[:,3] >= a[:,5]) if cascode else True)
    region = (a[:,0] >= .4-1e-9) & (a[:,0] <= 2.6+1e-9)
    error = float(np.max(np.abs(a[region,1]/40e-6-1)))
    at = int(np.argmin(abs(a[:,0]-1.65)))
    rout = float((a[at+1,0]-a[at-1,0])/(a[at+1,1]-a[at-1,1]))
    assert np.all(a[:,1] > 0) and np.all(np.diff(a[:,1]) > 0)
    result = {'W_L_um':[w,l], 'corner':corner, 'temp_C':temp,
              'max_error_0p4_2p6':error, 'meets_current_spec':bool(error <= .05),
              'all_range_saturated':bool(np.all(valid[region])),
              'first_saturated_grid_V':float(a[valid,0].min()),
              'rout_at_1p65_ohm':rout, 'current_at_1p65_A':float(a[at,1])}
    return result


def size_bias():
    q, = execute('reference-sizing', 'Ch05 reference sizing\n'+common()+
                 'Iref 0 b 40u\n'+mos('r','b','b')+
                 control('op\nwrdata op.txt v(b)'), ['op.txt'])
    csv('reference-sizing','scale,gate_V',q)
    resistor = (3.3-q[0,1])/40e-6
    # A first physical sizing estimate: at the desired VSG, current is roughly
    # proportional to W. Refine against the actual model, not a fitted square law.
    width = 1.0
    for step in range(3):
        a, = execute(f'pmos-sizing-{step}', 'Ch05 PMOS sizing at target VSG\n'+common()+
            'Vs s 0 3.3\nVg g 0 1.65\nVd d 0 1.65\n'+mos('p','d','g','s','s',w=width,p=True)+
            control('op\nlet ip = i(Vd)\nwrdata op.txt ip'), ['op.txt'])
        csv(f'pmos-sizing-{step}', 'scale,current_A', a)
        width *= 40e-6/a[0,1]
    return float(resistor), float(width)


def ota(name, resistor, wp, corner='typical', temp=27, ramp=False):
    base = 'Ch05 resistor-referenced OTA; 5 core MOS + 1 reference MOS\n'+common(corner,temp)
    base += '.options reltol=1e-8 abstol=1e-15 vntol=1e-11\n'
    base += 'Vdd vdd 0 '+('PWL(0 0 1u 3.3)' if ramp else '3.3')+'\n'
    base += f'Rref vdd b {resistor:.12g}\nVtail t dt 0\n'+mos('r','b','b')+mos('t','dt','b',w=20)
    base += 'Vcm cm 0 dc 1.4 ac 0\nVdiff diff 0 dc 0 ac 1\nEp ip cm diff 0 .5\nEn inn cm diff 0 -.5\n'
    base += mos('1','x','ip','t')+mos('2','o','inn','t')
    base += mos('3','x','x','vdd','vdd',w=wp,p=True)+mos('4','o','x','vdd','vdd',w=wp,p=True)
    params = ' '.join(f'@m.x{m}.m0[{p}]' for m in ('1','2','3','4','t') for p in ('gm','gmbs','gds','vdsat'))
    save = 'save all '+params+'\n'
    if ramp:
        a, = execute(name, base+'Cl o 0 1p\n'+control(save+'tran .02u 50u uic\nlet isupply = -i(Vdd)\nwrdata ramp.txt v(vdd) v(b) v(t) v(o) isupply'), ['ramp.txt'])
        csv(name,'time_s,supply_V,bias_V,tail_V,output_V,supply_A',a)
        assert abs(a[-1,4]-1.65) < .05 and a[-1,5] > 0
        return {'final_output_V':float(a[-1,4]), 'load_F':1e-12, 'supply_ramp_s':1e-6}
    body = save+'op\nlet isupply = -i(Vdd)\nwrdata op.txt v(x) v(o) v(t) v(b) isupply i(Vtail) '+params+'\n'
    body += 'ac lin 1 1 1\nwrdata dm.txt v(o)\nalter @vdiff[acmag] = 0\nalter @vcm[acmag] = 1\nac lin 1 1 1\nwrdata cm.txt v(o)\n'
    body += 'dc Vdiff -.0001 .0001 .0001\nwrdata linear.txt v(o)\ndc Vcm .7 2.8 .01\nwrdata common.txt v(x) v(o) v(t) '+ ' '.join(f'@m.x{m}.m0[vdsat]' for m in ('1','2','3','4','t'))+'\n'
    op, dm, cm, linear, sweep = execute(name,base+control(body),['op.txt','dm.txt','cm.txt','linear.txt','common.txt'])
    csv(name+'-op','scale,x_V,output_V,tail_V,bias_V,supply_A,tail_A,'+','.join(f'{m}_{p}' for m in ('1','2','3','4','t') for p in ('gm_S','gmb_S','gds_S','vdsat_V')),op)
    csv(name+'-dm','frequency_Hz,output_real,output_imag',dm)
    csv(name+'-cm','frequency_Hz,output_real,output_imag',cm)
    csv(name+'-linear','input_V,output_V',linear)
    csv(name+'-common','input_common_V,x_V,output_V,tail_V,vdsat1_V,vdsat2_V,vdsat3_V,vdsat4_V,vdsatT_V',sweep)
    x,o,t,b,powerI,it = op[0,1:7]
    pa = op[0,7:].reshape(5,4)
    margins = np.array([x-t, o-t, 3.3-x, 3.3-o,t])-pa[:,3]
    ir = (3.3-b)/resistor
    stamped = [('x','ip','t','0',*pa[0,:3]),('o','inn','t','0',*pa[1,:3]),
               ('x','x','0','0',*pa[2,:3]),('o','x','0','0',*pa[3,:3]),('t','0','0','0',*pa[4,:3])]
    predictions = {}
    for mode, values in [('dm',(.5,-.5)),('cm',(1,1))]:
        r=solve(['x','o','t'],{'0':0,'ip':values[0],'inn':values[1]},stamped)
        predictions[mode]=float(r['o'])
    actual = float(dm[0,1])
    slope = float((linear[-1,1]-linear[0,1])/.0002)
    assert np.isclose(actual,slope,rtol=.002), (actual,slope)
    assert np.isclose(actual,predictions['dm'],rtol=.01), (actual,predictions)
    assert np.isclose(cm[0,1],predictions['cm'],rtol=.05,atol=2e-4), (cm,predictions)
    valid = (sweep[:,1]-sweep[:,3]>=sweep[:,4]) & (sweep[:,2]-sweep[:,3]>=sweep[:,5]) & (3.3-sweep[:,1]>=sweep[:,6]) & (3.3-sweep[:,2]>=sweep[:,7]) & (sweep[:,3]>=sweep[:,8])
    assert np.any(valid)
    swing_range = None
    if name == 'ota':
        large, = execute('ota-large-signal',base+control(save+'dc Vdiff -.02 .02 .0001\nwrdata transfer.txt v(o) v(x) v(t) i(Vtail)'),['transfer.txt'])
        csv('ota-large-signal','input_difference_V,output_V,mirror_node_V,tail_V,tail_A',large)
        assert np.isclose(large[len(large)//2,1],o,atol=1e-6)
        swing, = execute('ota-output-compliance',base+'Vhold o 0 1.65\n'+control(save+'dc Vhold .1 3.2 .01\nwrdata swing.txt v(x) v(t) i(Vhold) '+ ' '.join(f'@m.x{m}.m0[vdsat]' for m in ('1','2','3','4','t'))),['swing.txt'])
        csv('ota-output-compliance','output_V,x_V,tail_V,external_hold_A,vdsat1_V,vdsat2_V,vdsat3_V,vdsat4_V,vdsatT_V',swing)
        valid_swing=(swing[:,1]-swing[:,2]>=swing[:,4]) & (swing[:,0]-swing[:,2]>=swing[:,5]) & (3.3-swing[:,1]>=swing[:,6]) & (3.3-swing[:,0]>=swing[:,7]) & (swing[:,2]>=swing[:,8])
        swing_range=[float(swing[valid_swing,0].min()),float(swing[valid_swing,0].max())]
    return {'corner':corner,'temp_C':temp,'output_V':float(o),'mirror_node_V':float(x),'tail_V':float(t),'bias_V':float(b),
            'tail_A':float(it),'reference_A':float(ir),'power_W':float(powerI*3.3),
            'dm_gain':actual,'cm_gain':float(cm[0,1]),'nodal_reduced_gain':predictions,
            'saturation_margins_V':list(map(float,margins)),
            'free_output_valid_CM_grid_V':[float(sweep[valid,0].min()),float(sweep[valid,0].max())],
            'forced_output_saturated_grid_V':swing_range,
            'output_sat_limits_at_Q_V':[float(t+pa[1,3]),float(3.3-pa[3,3])],
            'approx_gain':float(pa[0,0]/(pa[1,2]+pa[3,2]))}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    model=verify_models()
    assert SPEC['supply_V']==3.3 and SPEC['temperature_C']==27
    assert SPEC['mirror']['reference_A']==40e-6 and SPEC['mirror']['target_A']==40e-6
    assert SPEC['mirror']['output_range_V']==[.4,2.6] and SPEC['mirror']['max_relative_error']==.05
    assert SPEC['ota']['input_common_V']==1.4
    old=json.loads((DATA/'metrics.json').read_text()) if args.check else None
    mirrors={}
    for name,w,l in [('short',2.8,.28),('medium',10,1),('long',20,2),('cascode',10,1)]:
        mirrors[name]=mirror(name,w,l,name=='cascode')
    # A failed short design is expected and retained; passing is not defined by
    # changing the requested current/voltage window after inspecting the data.
    assert not mirrors['short']['meets_current_spec']
    assert mirrors['medium']['meets_current_spec'] and mirrors['medium']['all_range_saturated']
    assert mirrors['long']['meets_current_spec'] and mirrors['long']['all_range_saturated']
    assert 3.3*80e-6 <= SPEC['mirror']['two_branch_supply_budget_W']
    resistor,wp=size_bias()
    q=ota('ota',resistor,wp)
    s=SPEC['ota']
    assert abs(q['output_V']-s['output_target_V'])<=s['output_target_tolerance_V']
    assert abs(q['tail_A']/s['nominal_tail_A']-1)<=s['tail_relative_tolerance']
    assert q['dm_gain']>=s['minimum_low_frequency_gain_V_V'] and q['power_W']<=s['supply_budget_W']
    assert min(q['saturation_margins_V'])>0
    pvt=[]
    for tag,corner,temp in [('ss','ss',27),('ff','ff',27),('cold','typical',-20),('hot','typical',85)]:
        pvt.append({'mirror':mirror('long-'+tag,20,2,corner=corner,temp=temp),
                    'ota':ota('ota-'+tag,resistor,wp,corner,temp)})
    ramp=ota('ota-startup',resistor,wp,ramp=True)
    metrics={'design':SPEC,'mirrors':mirrors,'reference_resistor_ohm':resistor,'pmos_width_um':wp,
             'ota':q,'pvt_smoke':pvt,'startup_one_ramp':ramp}
    if old:
        for k in ('dm_gain','tail_A','output_V'):
            assert np.isclose(q[k],old['ota'][k],rtol=.01), ('Reference drift',k)
    DATA.mkdir(parents=True,exist_ok=True)
    (DATA/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8',newline='\n')
    tracked=[Path(__file__),LAB/'design.json',ROOT/'scripts/run.py',ROOT/'scripts/check_teaching.py',ROOT/'scripts/check_mirrors.py']
    tracked+=sorted((LAB/'decks').glob('*.cir'))+sorted((LAB/'logs').glob('*.txt'))+sorted(DATA.glob('*.csv'))+[DATA/'metrics.json']
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    record={'executed_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.system(),'python':platform.python_version(),
            'ngspice':subprocess.run([simulator(),'--version'],capture_output=True,text=True,check=True).stdout.strip(),
            'executable_sha256':digest(Path(simulator())),'model':model,'junction_geometry':{'AD_AS_m2':5e-12,'PD_PS_m':21e-6},
            'statistical_global':0,'statistical_mismatch':0,'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in tracked}}
    (DATA/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'mirrors':mirrors,'Rref':resistor,'Wp':wp,'ota':q,'PVT':[(p['ota']['corner'],p['ota']['temp_C'],p['ota']['output_V']) for p in pvt]},indent=2))
    print('PASS: mirror design constraints, OTA operating point/saturation/power/gain, DC-AC/nodal checks, PVT smoke and one supply ramp.')


if __name__=='__main__':main()
