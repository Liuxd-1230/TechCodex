"""Export two verified Chapter 5 DC sweeps; no simulator in the browser."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'模拟/实验/电流镜'
OUT=ROOT/'web/assets/demos/mirror-data.json'


def package():
    run=json.loads((LAB/'data/run.json').read_text(encoding='utf-8'))
    result={'schema':1,'source':'Windows native ngspice-47 / GF180MCU',
            'model_commit':run['model']['commit'],'executed_utc':run['executed_utc'],
            'conditions':{'VDD_V':3.3,'Iref_A':40e-6,'W_L_um':[10,1],'corner':'typical','temp_C':27,'statistical_global':0,'statistical_mismatch':0},
            'columns':['output_V','current_A','gate_V','internal_V','bottom_vdsat_V','upper_vdsat_V'],
            'source_sha256':{},'curves':{}}
    for name in ('medium','cascode'):
        path=LAB/'data'/(name+'.csv')
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert run['sha256'][path.relative_to(ROOT).as_posix()]==digest
        result['source_sha256'][name+'.csv']=digest
        with path.open(encoding='ascii',newline='') as stream:
            result['curves'][name]=[[float(x) for x in row] for row in list(csv.reader(stream))[1:]]
    return json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    content=package()
    if args.check:
        assert OUT.read_bytes()==content.encode('utf-8'),'Mirror payload stale'
        print('PASS: mirror browser data matches archived native-SPICE sweeps.')
    else:OUT.write_text(content,encoding='utf-8',newline='\n')
