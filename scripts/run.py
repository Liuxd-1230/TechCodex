"""Run real GF180MCU experiments, preserve logs/decks, and check physics."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

import numpy as np
from bootstrap import ROOT, simulator, verify_models

LAB = ROOT / '模拟/实验'
DATA = LAB / 'data'


def run_deck(name, source, expected):
    work = ROOT / 'build' / name
    work.mkdir(parents=True, exist_ok=True)
    for file in ('design.ngspice', 'sm141064.ngspice'):
        shutil.copyfile(ROOT / 'models/gf180mcu' / file, work / file)
    deck = work / 'run.cir'
    deck.write_text(source, encoding='ascii', newline='\n')
    for file in expected:
        (work / file).unlink(missing_ok=True)  # prevent a stale output from passing
    result = subprocess.run([simulator(), '-n', '-b', deck.name], cwd=work,
                            capture_output=True, text=True, errors='replace', timeout=90)
    log = result.stdout + '\n' + result.stderr
    (work / 'ngspice.log').write_text(f'exit_code={result.returncode}\n'+log, encoding='utf-8',newline='\n')
    if result.returncode or re.search(r'(?im)^\s*(error|fatal)|timestep too small|singular matrix|unknown (device|parameter)|not found', log):
        raise RuntimeError(f'{name} failed (exit={result.returncode}); inspect build/{name}/ngspice.log\n{log[-2000:]}')
    out = []
    for file in expected:
        path = work / file
        a = np.loadtxt(path, skiprows=1, ndmin=2)
        if not np.isfinite(a).all() or not a.size:
            raise RuntimeError(f'{name}: invalid numerical output')
        out.append(a)
    return out


def common(corner='typical', temp=27):
    return ('.include "design.ngspice"\n'
            f'.lib "sm141064.ngspice" {corner}\n'
            '.param sw_stat_global=0 sw_stat_mismatch=0\n'
            f'.temp {temp}\n.options reltol=1e-5 abstol=1e-13 vntol=1e-8\n')


def write_csv(name, header, a):
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / name).open('w',encoding='ascii',newline='\n') as stream:
        np.savetxt(stream, a, delimiter=',', header=header, comments='', fmt='%.12e')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='also compare with committed reference metrics')
    args = parser.parse_args()
    model = verify_models()
    reference = DATA / 'metrics.json'
    if args.check and not reference.exists():
        raise FileNotFoundError('--check requires a committed reference metrics.json')
    old = json.loads(reference.read_text(encoding='utf-8')) if args.check and reference.exists() else None
    metrics = {}
    transfer = (LAB / 'v0-device.cir').read_text(encoding='utf-8')
    for length in (0.28, 1.0, 2.0):
        a, = run_deck(f'transfer-L{length:g}', transfer.replace('@LENGTH@', f'{length}u'), ['transfer.txt'])
        # columns: Vg, Id, gm, gds, gmbs, vth, vdsat
        if len(a) != 241 or not np.all(np.diff(a[:, 1]) > 0):
            raise AssertionError('Unexpected transfer sweep shape or nonmonotonic Id')
        write_csv(f'transfer-L{length:g}.csv', 'vgs_V,id_A,gm_S,gds_S,gmb_S,vth_V,vdsat_V', a)
        i = int(np.argmin(abs(a[:, 0] - .9)))
        row = a[i]
        gm_fd = (a[i+1, 1]-a[i-1, 1])/(a[i+1, 0]-a[i-1, 0])
        if not np.isclose(gm_fd, row[2], rtol=.01):
            raise AssertionError('gm differs from finite difference')
        metrics[f'L{length:g}'] = dict(zip(('vgs_V','id_A','gm_S','gds_S','gmb_S','vth_V','vdsat_V'), map(float,row)))
        metrics[f'L{length:g}']['gm_fd_S'] = float(gm_fd)

    output = (LAB / 'v0-output.cir').read_text(encoding='utf-8')
    for vg in (.8, .9, 1.1, 1.3):
        a, = run_deck(f'output-Vg{vg:g}', output.replace('@VG@', str(vg)), ['output.txt'])
        write_csv(f'output-Vg{vg:g}.csv', 'vds_V,id_A,gds_S', a)
        if vg == .9:
            i = int(np.argmin(abs(a[:,0]-1.65)))
            gds_fd = (a[i+1,1]-a[i-1,1])/(a[i+1,0]-a[i-1,0])
            if not np.isclose(gds_fd, a[i,2], rtol=.01):
                raise AssertionError('gds differs from finite difference')
            metrics['L1']['gds_fd_S'] = float(gds_fd)

    body = (LAB / 'v0-body.cir').read_text(encoding='utf-8')
    a, = run_deck('body', body, ['body.txt'])
    write_csv('body.csv', 'vsb_V,id_A,gm_S,gmb_S,vth_V', a)
    if not a[-1,4] > a[0,4]:
        raise AssertionError('Body bias should raise NMOS threshold here')

    # Smoke coverage: both polarities, three corners, three temperatures.
    pvt = []
    for corner in ('typical','ff','ss'):
        for temp in (-40,27,125):
            source = 'GF180 PVT compatibility smoke\n' + common(corner,temp) + '''
Vdn dn 0 1.65
Vgn gn 0 .9
Vsp sp 0 3.3
Vdp dp 0 1.65
Vgp gp 0 2.4
Xn dn gn 0 0 nmos_3p3 w=10u l=1u
Xp dp gp sp sp pmos_3p3 w=10u l=1u
.control
set noaskquit
set wr_singlescale
set wr_vecnames
op
wrdata pvt.txt @m.xn.m0[id] @m.xp.m0[id]
quit
.endc
.end
'''
            b, = run_deck(f'pvt-{corner}-{temp}', source, ['pvt.txt'])
            if np.any(np.abs(b[0,1:]) < 1e-9):
                raise AssertionError('PVT smoke transistor is off')
            pvt.append({'corner':corner,'temp_C':temp,'nmos_id_A':float(b[0,1]),'pmos_id_A':float(b[0,2])})
    metrics['pvt_smoke'] = pvt

    cs = (LAB / 'v1-common-source.cir').read_text(encoding='utf-8')
    for rs in (0,1000):
        source = cs.replace('@RS@',str(rs))
        if rs == 0:
            source = source.replace('Rs src 0 0\n','Vshort src 0 0\n')
        op, dc, ac, tran = run_deck(f'cs-Rs{rs}', source,
                                  ['op.txt','dc.txt','ac.txt','tran.txt'])
        # op scale, out, source, Id, gm, gds, gmb, Vdsat
        _, vo, vs, current, gm, gds, gmb, vdsat = op[0]
        denom = 1 + (gm+gmb)*rs + gds*(39000+rs)
        prediction = -gm*39000/denom
        derivative = (dc[-1,1]-dc[0,1])/(dc[-1,0]-dc[0,0])
        gain = ac[0,1]
        if vo-vs < vdsat or current <= 0:
            raise AssertionError('Common-source transistor bias is invalid')
        if not np.isclose(prediction,gain,rtol=.003) or not np.isclose(derivative,gain,rtol=.003):
            raise AssertionError('KCL / DC finite difference / low-frequency AC disagree')
        mag = np.hypot(ac[:,1],ac[:,2])
        target = mag[0]/np.sqrt(2)
        j = np.flatnonzero(mag <= target)[0]
        fc = float(np.exp(np.interp(target,mag[j-1:j+1][::-1],np.log(ac[j-1:j+1,0])[::-1])))
        metrics[f'cs_Rs{rs}'] = dict(vout_V=float(vo),vsource_V=float(vs),id_A=float(current),
                                   gm_S=float(gm),gds_S=float(gds),gmb_S=float(gmb),vdsat_V=float(vdsat),
                                   kcl_gain=float(prediction),ac_gain=float(gain),dc_gain=float(derivative),f3db_Hz=fc)
        write_csv(f'cs-Rs{rs}-ac.csv','frequency_Hz,gain_real,gain_imag',ac)
        write_csv(f'cs-Rs{rs}-tran.csv','time_s,vin_V,vout_V',tran)

    if old:
        for case in ('L0.28','L1','L2','cs_Rs0','cs_Rs1000'):
            for key,value in old[case].items():
                if not np.isclose(metrics[case][key],value,rtol=.02,atol=1e-12):
                    raise AssertionError(f'Reference drift >2%: {case}.{key}')
    reference.write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8',newline='\n')
    version = subprocess.run([simulator(),'--version'],capture_output=True,text=True,errors='replace',check=True).stdout
    # Archive portable provenance; absolute executable paths stay in ignored build/.
    record = {'executed_utc':datetime.now(timezone.utc).isoformat(),
              'platform':platform.system(),'machine':platform.machine(),'python':platform.python_version(),
              'numpy':np.__version__,'ngspice_version':version.strip(),'model_commit':model['commit'],
              'ngspice_executable_sha256':hashlib.sha256(Path(simulator()).read_bytes()).hexdigest(),
              'model_sha256':model['files'],'conditions':{'temp_C':27,'corner':'typical','stat_global':0,'stat_mismatch':0,
              'W_um':10,'L_um':[.28,1,2],'transfer_Vds_V':1.65,'junction_AD_AS_m2':5e-12,'junction_PD_PS_m':21e-6},
              'netlist_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in LAB.glob('*.cir')},
              'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'expanded_deck_sha256':{p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (ROOT/'build').glob('*/run.cir') if p.parent.name != 'probe'},
              'data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.iterdir()
                  if p.suffix=='.csv' or p.name=='metrics.json'},
              'checks':['model hashes','finite data','transfer monotonicity','gm and gds finite differences',
                        'body threshold trend','NMOS/PMOS 3 corners x 3 temperatures smoke',
                        'CS bias','KCL vs AC vs DC gain <0.3%']}
    (DATA/'run.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in metrics.items() if k.startswith('cs_')},indent=2))
    print('PASS: 19 native ngspice decks; all physical consistency checks passed.')


if __name__ == '__main__':
    main()
