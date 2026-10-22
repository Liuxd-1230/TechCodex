"""Package the existing, hashed ngspice sweep for the browser; never run a simulator."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / '模拟/实验/差分对'
OUT = ROOT / 'web/assets/demos/steering-data.json'
COLUMNS = ['input_V', 'i1_A', 'i2_A', 'o1_V', 'o2_V', 'tail_V',
           'vdsat1_V', 'vdsat2_V', 'is1_A', 'is2_A', 'body_return_A']


def package():
    run = json.loads((LAB / 'data/run.json').read_text(encoding='utf-8'))
    sources = ['data/ideal-steering-sweep.csv', 'data/metrics.json', 'data/run.json']
    hashes = {p: hashlib.sha256((LAB / p).read_bytes()).hexdigest() for p in sources}
    for p in sources[:2]:
        key = (LAB / p).relative_to(ROOT).as_posix()
        if run['sha256'][key] != hashes[p]:
            raise ValueError(f'Unverified simulation source: {p}')
    metrics = json.loads((LAB / 'data/metrics.json').read_text(encoding='utf-8'))['ideal']
    c = run['conditions']
    slope = abs(metrics['gains']['dm']['diff']) / c['RD_ohm']
    vov = c['nominal_tail_A'] / slope
    meta = {
        'schema': 1, 'source': 'GF180MCU / Windows native ngspice-47',
        'model_commit': run['model_commit'], 'executed_utc': run['executed_utc'],
        'source_sha256': hashes, 'conditions': c,
        'analytic': {'beta_A_V2': slope**2 / c['nominal_tail_A'],
                     'threshold_V': c['nominal_VCM_V'] - metrics['tail_V'] - vov,
                     'port_slope_A_V': slope},
        'columns': COLUMNS,
    }
    with (LAB / sources[0]).open(encoding='utf-8', newline='') as stream:
        rows = [[float(row[k]) for k in COLUMNS] for row in csv.DictReader(stream)]
    # Keep each sample on one line for reviewable diffs, and LF on Windows too.
    header = json.dumps(meta, ensure_ascii=False, indent=2)
    return header[:-2] + ',\n  "rows": [\n' + ',\n'.join(
        '    ' + json.dumps(row, separators=(',', ':')) for row in rows) + '\n  ]\n}\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = package()
    if args.check:
        if not OUT.is_file() or OUT.read_bytes() != content.encode('utf-8'):
            raise SystemExit('Demo payload is stale; run scripts/export_steering_demo.py')
        print('PASS: browser payload matches verified ngspice CSV, calibration and provenance.')
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(content, encoding='utf-8', newline='\n')
        print(f'Exported {OUT.relative_to(ROOT)}')
