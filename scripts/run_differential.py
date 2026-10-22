"""Run Chapter 4's controlled current-steering/common-mode comparisons on native SPICE."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess

import numpy as np
from bootstrap import ROOT, simulator, verify_models
from check_teaching import solve
from run import common, run_deck

LAB=ROOT/'模拟/实验/差分对'
DATA=LAB/'data'
IT=80e-6
RCM=1.4


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(name,source,expected):
    arrays=run_deck('ch04/'+name,source,expected)
    work=ROOT/'build/ch04'/name
    for folder in ('logs','decks'):
        (LAB/folder).mkdir(parents=True,exist_ok=True)
    shutil.copyfile(work/'ngspice.log',LAB/'logs'/f'{name}.txt')
    shutil.copyfile(work/'run.cir',LAB/'decks'/f'{name}.cir')
    return arrays


def write_csv(name,header,data):
    DATA.mkdir(parents=True,exist_ok=True)
    # Match the repository's LF policy before hashing, including on Windows.
    with (DATA/(name+'.csv')).open('w',encoding='ascii',newline='\n') as stream:
        np.savetxt(stream,data,delimiter=',',header=header,comments='',fmt='%.12e')


def pair(name,tail_voltage=None,mismatch=False,steering=False):
    mos=tail_voltage is not None
    replacements={
        '@R1@':'20100' if mismatch else '20000',
        '@R2@':'19900' if mismatch else '20000',
        '@TAIL@':(f'Vbias vb 0 {tail_voltage:.14g}\n'
                  'XT t vb 0 0 nmos_3p3 w=10u l=.28u ad=5p as=5p pd=21u ps=21u') if mos else 'Itail t 0 80u',
        '@TAILSAVE@':'@m.xt.m0[gds] @m.xt.m0[vdsat]' if mos else '',
        '@TAILOP@':'@m.xt.m0[gds] @m.xt.m0[vdsat]' if mos else 'v(diff) v(diff)',
        '@TAILSWEEP@':'@m.xt.m0[vdsat]' if mos else 'v(diff)',
        '@SWEEP@':'Vdiff -.65 .65 .002' if steering else 'Vcm .75 3.3 .005',
    }
    source=(LAB/'pair.cir').read_text(encoding='ascii')
    for old,new in replacements.items():source=source.replace(old,new)
    source='\n'.join(line.rstrip() for line in source.splitlines())+'\n'
    op,adm,acm,linear_dm,linear_cm,sweep=execute(name,source,['op.txt','adm.txt','acm.txt','linear_dm.txt','linear_cm.txt','sweep.txt'])
    q=op[0,1:]
    # OP: o1,o2,t,I1,I2,gm1,gmb1,gds1,gm2,gmb2,gds2,gtail,VdsatT
    params=q[5:11].reshape(2,3)
    rs=[20100,19900] if mismatch else [20000,20000]
    transistors=[('o1','ip','t','0',*params[0]),('o2','inn','t','0',*params[1])]
    resistors=[('o1','0',rs[0]),('o2','0',rs[1])]
    if mos:resistors.append(('t','0',1/q[11]))
    gains={}
    reduced_model={}
    for label,ac,linear,inputs in [('dm',adm,linear_dm,(.5,-.5)),('cm',acm,linear_cm,(1,1))]:
        nodal=solve(['o1','o2','t'],{'0':0,'ip':inputs[0],'inn':inputs[1]},transistors,resistors)
        prediction=np.array([nodal['o1'],nodal['o2'],nodal['t'],nodal['o1']-nodal['o2']])
        actual=ac[0,1::2]  # real parts; each complex output has a real/imag pair
        if label=='dm' and not np.allclose(actual,prediction,rtol=.005,atol=1e-7):
            raise AssertionError((name,label,actual,prediction))
        reduced_model[label]=dict(zip(('o1','o2','tail','diff'),map(float,prediction)))
        dc_slope=(linear[-1,1:]-linear[0,1:])/(linear[-1,0]-linear[0,0])
        dc_slope=np.append(dc_slope,dc_slope[0]-dc_slope[1])
        if not np.allclose(actual,dc_slope,rtol=.0002,atol=3e-6):raise AssertionError((name,'DC/AC',actual,dc_slope))
        gains[label]=dict(zip(('o1','o2','tail','diff'),map(float,actual)))
        write_csv(name+'-'+label,'frequency_Hz,o1_real,o1_imag,o2_real,o2_imag,tail_real,tail_imag,diff_real,diff_imag',ac)
        write_csv(name+'-linear-'+label,'input_V,o1_V,o2_V,tail_V',linear)
    current=sweep[:,4]+sweep[:,5]
    if not np.allclose((3.3-sweep[:,1])/rs[0],sweep[:,4],atol=2e-11):raise AssertionError('R1 KCL')
    if not np.allclose((3.3-sweep[:,2])/rs[1],sweep[:,5],atol=2e-11):raise AssertionError('R2 KCL')
    if not mos and not np.allclose(sweep[:,9]+sweep[:,10],IT,rtol=1e-7,atol=1e-12):raise AssertionError('Ideal tail source-terminal KCL')
    if not np.allclose(current-sweep[:,9]-sweep[:,10],sweep[:,11],atol=3e-12):raise AssertionError('Body-return terminal KCL')
    if steering:
        if not np.allclose(sweep[:,4],sweep[::-1,5],rtol=2e-5,atol=2e-10):raise AssertionError('Exchange symmetry')
        centre=len(sweep)//2
        slope=((sweep[centre+1,1]-sweep[centre+1,2])-(sweep[centre-1,1]-sweep[centre-1,2]))/.004
        if not np.isclose(slope,gains['dm']['diff'],rtol=.002):raise AssertionError('DC/AC slope')
        # Only require strong-current devices to retain a saturation margin.
        for i in (1,2):
            on=sweep[:,3+i] > IT*.05
            if np.any((sweep[:,i]-sweep[:,3]-sweep[:,5+i])[on] < 0):raise AssertionError('Steering sweep exits saturation')
    write_csv(name+'-sweep','input_V,o1_V,o2_V,tail_V,i1_A,i2_A,vdsat1_V,vdsat2_V,vdsat_tail_V,is1_A,is2_A,body_return_A',sweep)
    write_csv(name+'-op','scale,o1_V,o2_V,tail_V,i1_A,i2_A,gm1_S,gmb1_S,gds1_S,gm2_S,gmb2_S,gds2_S,gtail_S,vdsat_tail_V,body_return_A',op)
    return dict(zip(('o1_V','o2_V','tail_V','i1_A','i2_A','gm1_S','gmb1_S','gds1_S','gm2_S','gmb2_S','gds2_S','gtail_S','vdsat_tail_V','body_return_A'),map(float,q)))|{'gains':gains,'reduced_model':reduced_model},sweep


def calibrate(tail_node):
    # Calibrate the real tail at the SAME voltage, current, geometry and temperature
    # as the ideal-tail pair. No later retuning along the common-mode sweep.
    source=('Ch04 real-tail calibration\n'+common()+f'Vdr d 0 {tail_node:.14g}\n'
            'Vb b 0 .7\nXT d b 0 0 nmos_3p3 w=10u l=.28u ad=5p as=5p pd=21u ps=21u\n'
            '.control\nset noaskquit\nset wr_singlescale\nset wr_vecnames\n'
            'save all @m.xt.m0[gm]\ndc Vb .4 1.2 .001\nlet current = -i(Vdr)\n'
            'wrdata cal.txt current @m.xt.m0[gm]\nquit\n.endc\n.end\n')
    data,=execute('calibrate',source,['cal.txt'])
    write_csv('tail-calibration','gate_V,drain_A,gm_S',data)
    voltage=float(np.interp(IT,data[:,1],data[:,0]))
    # Newton refinement with an independently executed operating point.
    refinement=source[:source.index('.control')].replace('Vb b 0 .7',f'Vb b 0 {voltage:.14g}')+(
        '.control\nset noaskquit\nset wr_singlescale\nset wr_vecnames\nop\n'
        'let current = -i(Vdr)\nwrdata cal.txt current @m.xt.m0[gm]\nquit\n.endc\n.end\n')
    data,=execute('calibrate-refine',refinement,['cal.txt'])
    write_csv('tail-calibration-refine','drain_V,drain_A,gm_S',data)
    return voltage+(IT-data[0,1])/data[0,2]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    model=verify_models()
    metrics_path=DATA/'metrics.json'
    old=json.loads(metrics_path.read_text()) if args.check and metrics_path.exists() else None
    if args.check and old is None:raise FileNotFoundError('--check needs committed Chapter 4 metrics')
    ideal,_=pair('ideal-steering',steering=True)
    tail_gate=calibrate(ideal['tail_V'])
    cmideal,_=pair('ideal-common')
    real,real_sweep=pair('mos-common',tail_voltage=tail_gate)
    unequal,_=pair('mos-unequal-load',tail_voltage=tail_gate,mismatch=True)
    if not np.allclose([real['i1_A'],real['i2_A']],[ideal['i1_A'],ideal['i2_A']],rtol=2e-6):raise AssertionError('Calibration failed')
    if not np.allclose([real['o1_V'],real['tail_V']],[ideal['o1_V'],ideal['tail_V']],atol=3e-6):raise AssertionError('Uncontrolled bias difference')
    if abs(real['gains']['cm']['diff'])>1e-7:raise AssertionError('Matched pair common-to-diff symmetry')
    valid=(real_sweep[:,3]>=real_sweep[:,8]) & (real_sweep[:,1]-real_sweep[:,3]>=real_sweep[:,6])
    valid_cm=real_sweep[valid,0]
    metrics={'tail_gate_V':float(tail_gate),'ideal':ideal,'ideal_common':cmideal,'mos':real,'unequal':unequal,
             'mos_valid_cm_grid_V':[float(valid_cm.min()),float(valid_cm.max())],
             'valid_cm_definition':'VDS >= ngspice operating-point VDSAT for all three MOS, DC grid only; not a distortion/compliance specification'}
    if old:
        for case in ('ideal','mos','unequal'):
            for mode in ('dm','cm'):
                for node in ('o1','o2','tail','diff'):
                    if not np.isclose(metrics[case]['gains'][mode][node],old[case]['gains'][mode][node],rtol=.02,atol=1e-7):
                        raise AssertionError(f'Reference drift: {case}/{mode}/{node}')
    metrics_path.write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8',newline='\n')
    version=subprocess.run([simulator(),'--version'],capture_output=True,text=True,errors='replace',check=True).stdout.strip()
    tracked=[LAB/'pair.cir',Path(__file__),ROOT/'scripts/run.py',ROOT/'scripts/check_teaching.py']
    tracked += sorted((LAB/'decks').glob('*.cir'))+sorted((LAB/'logs').glob('*.txt'))+sorted(DATA.glob('*.csv'))+[metrics_path]
    record={'executed_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.system(),
            'python':platform.python_version(),'numpy':np.__version__,'ngspice':version,
            'executable_sha256':digest(Path(simulator())),'model_commit':model['commit'],'model_sha256':model['files'],
            'conditions':{'VDD_V':3.3,'nominal_VCM_V':RCM,'nominal_tail_A':IT,'RD_ohm':20000,
                          'input_W_L_um':[10,1],'tail_W_L_um':[10,.28],'temp_C':27,'corner':'typical',
                          'sw_stat_global':0,'sw_stat_mismatch':0,'AD_AS_m2':5e-12,'PD_PS_m':21e-6,
                          'AC_Hz':1,'resistor_delta_ohm':[100,-100]},
            'sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in tracked},
            'checks':['model hashes','finite data','branch KCL','ideal tail conservation','exchange symmetry',
                      'conducting input devices saturation','complete-model DC vs AC slopes','reduced three-parameter nodal DM approximation <0.5%',
                      'same nominal bias for ideal/MOS tail','matched common-to-differential cancellation']}
    (DATA/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'tail_gate_V':tail_gate,'valid_CM_grid_V':metrics['mos_valid_cm_grid_V'],
                      'ideal_gain':ideal['gains'],'mos_gain':real['gains'],'unequal_gain':unequal['gains']},indent=2))
    print('PASS: Chapter 4 current steering and controlled tail comparison; 6 native ngspice decks.')


if __name__=='__main__':main()
