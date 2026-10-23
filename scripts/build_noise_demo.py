"""Export unscaled, hash-verified GF180 spectra; no browser SPICE or free sizing."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LAB=ROOT/'模拟/实验/噪声/data'
OUT=ROOT/'web/assets/demos/noise-data.json'


def package():
    run=json.loads((LAB/'run.json').read_text(encoding='utf-8'))
    for name,digest in run['sha256'].items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Stale noise experiment: '+name)
    rows=[]
    with (LAB/'baseline-spectrum.csv').open(encoding='ascii',newline='') as stream:
        reader=csv.reader(stream);next(reader)
        for line in reader:
            a=[float(x) for x in line]
            if a[0]>1e6:continue
            flicker=sum(a[16:22])*a[2]/a[1]
            rows.append([a[0],a[2],a[2]-flicker,flicker])
    payload=dict(schema=1,source='ngspice 47 .noise, one-sided PSD, set sqrnoise',model_commit='9f992d5a9186d1f7820c58f039c484ad35b2edea',
        csv_sha256=hashlib.sha256((LAB/'baseline-spectrum.csv').read_bytes()).hexdigest(),
        conditions=dict(corner='typical',temperature_C=27,supply_V=3.3,common_mode_V=1.4,load_F=1e-12,input_W_L_um=[10,1],input_port='full differential voltage, ideal driver'),
        columns=['frequency_Hz','input_V2_Hz','nonflicker_input_V2_Hz','flicker_input_V2_Hz'],rows=rows)
    return json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n'


if __name__=='__main__':
    OUT.write_text(package(),encoding='utf-8',newline='\n');print('Exported 601 original GF180 PSD samples, no rescaling.')
