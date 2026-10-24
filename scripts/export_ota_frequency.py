"""Package the archived Chapter 6 GF180 AC cases without interpolation."""
import argparse
import cmath
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / '模拟/实验/频率响应'
DATA = LAB / 'data'
OUT = ROOT / 'web/assets/demos/ota-frequency-data.json'

CASE_DETAILS = {
    'ota-unloaded': {
        'group': 'load', 'label': '无外接 CL',
        'change': '第 5 章基准尺寸与偏置；无外接负载电容。器件寄生仍保留。',
        'deck_load_note': '网表用 1e-24 F 表示无外接电容。',
    },
    'ota-1p': {
        'group': 'baseline', 'label': '基准 · 1 pF',
        'change': '第 5 章基准尺寸与偏置，仅在输出增加 1 pF。',
        'deck_load_note': None,
    },
    'ota-5p': {
        'group': 'load', 'label': '负载 · 5 pF',
        'change': '相对基准只将输出电容从 1 pF 改为 5 pF。',
        'deck_load_note': None,
    },
    'ota-wide': {
        'group': 'design', 'label': '输入管 W 加倍',
        'change': 'M1、M2 的 W 从 10 增至 20 µm；L、尾管、参考支路保持基准值。',
        'deck_load_note': None,
    },
    'ota-long': {
        'group': 'design', 'label': '核心 W/L 同比加倍',
        'change': 'NMOS M1、M2 的 W/L 从 10/1 增至 20/2 µm；PMOS M3、M4 从 3.708/1 增至 7.416/2 µm。尾管和参考支路不变。',
        'deck_load_note': None,
    },
    'ota-current': {
        'group': 'design', 'label': '全部 MOS W 加倍',
        'change': '全部 MOS 的 W 加倍、RREF 减半，L 不变；电流随之增加。',
        'deck_load_note': None,
    },
}

VISIBLE_CASES = {
    'load': {'baseline': 'ota-1p', 'candidates': ['ota-unloaded', 'ota-5p']},
    'design': {'baseline': 'ota-1p', 'candidates': ['ota-wide', 'ota-long', 'ota-current']},
}
AC_COLUMNS = ['frequency_Hz', 'v(o)_real', 'v(o)_imag']


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_run(run):
    for relative, expected in run['sha256'].items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError(f'Frequency run source is missing or outside repository: {relative}')
        if sha256(path) != expected:
            raise ValueError(f'Frequency run source hash changed: {relative}')


def unwrap_phase(rows):
    phases = []
    previous = None
    offset = 0.0
    for row in rows:
        principal = cmath.phase(complex(row[1], row[2]))
        if previous is not None:
            delta = principal - previous
            if delta > math.pi:
                offset -= 2 * math.pi
            elif delta < -math.pi:
                offset += 2 * math.pi
        phases.append(math.degrees(principal + offset))
        previous = principal
    return phases


def read_ac(case_id):
    path = DATA / f'{case_id}-ac.csv'
    lines = path.read_text(encoding='ascii').splitlines()
    columns = lines[0].split(',')
    if columns[:3] != AC_COLUMNS:
        raise ValueError(f'Unexpected output columns in {path.relative_to(ROOT)}')
    rows = [[float(value) for value in line.split(',')[:3]] for line in lines[1:] if line]
    if not rows or any(len(row) != 3 for row in rows):
        raise ValueError(f'Invalid AC rows in {path.relative_to(ROOT)}')
    if any(rows[i][0] >= rows[i + 1][0] for i in range(len(rows) - 1)):
        raise ValueError(f'AC frequencies are not strictly increasing: {path.relative_to(ROOT)}')
    return path, rows


def package():
    run_path = DATA / 'run.json'
    run = json.loads(run_path.read_text(encoding='utf-8'))
    verify_run(run)
    metrics_path = DATA / 'metrics.json'
    design_path = LAB / 'design.json'
    metrics = json.loads(metrics_path.read_text(encoding='utf-8'))
    design = json.loads(design_path.read_text(encoding='utf-8'))

    cases = {}
    source_paths = [metrics_path, design_path]
    expected_frequencies = None
    for case_id, details in CASE_DETAILS.items():
        ac_path, rows = read_ac(case_id)
        op_path = DATA / f'{case_id}-op.csv'
        if not op_path.is_file() or case_id not in metrics:
            raise ValueError(f'Missing operating-point or metrics source for {case_id}')
        source_paths.extend((ac_path, op_path))
        frequencies = [row[0] for row in rows]
        if expected_frequencies is None:
            expected_frequencies = frequencies
        elif frequencies != expected_frequencies:
            raise ValueError(f'AC frequency grid differs for {case_id}')

        phases = unwrap_phase(rows)
        points = []
        for row, phase in zip(rows, phases):
            frequency, real, imag = row
            magnitude = math.hypot(real, imag)
            points.append([frequency, 20 * math.log10(magnitude) if magnitude else -math.inf, phase])
        if not all(math.isfinite(value) for point in points for value in point):
            raise ValueError(f'Non-finite response value in {case_id}')

        record = metrics[case_id]
        displayed_metrics = {
            key: record[key]
            for key in ('gain_V_V', 'bandwidth_3dB_Hz', 'unity_Hz', 'power_W')
        }
        case = {
            'label': details['label'],
            'change': details['change'],
            'group': details['group'],
            'external_load_F': record['load_F'],
            'metrics': displayed_metrics,
            'ac_csv': ac_path.relative_to(ROOT).as_posix(),
            'columns': ['frequency_Hz', 'gain_dB', 'phase_deg_unwrapped'],
            'points': points,
        }
        if details['deck_load_note']:
            case['deck_load_note'] = details['deck_load_note']
        cases[case_id] = case

    if len(expected_frequencies) != 801 or expected_frequencies[0] != 1 or expected_frequencies[-1] != 1e10:
        raise ValueError('Expected the archived 801-point 1 Hz–10 GHz AC sweep')

    source_sha256 = {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_paths}
    return {
        'schema': 1,
        'source': 'Windows native ngspice-47 / GF180MCU BSIM4',
        'model_commit': run['model']['commit'],
        'executed_utc': run['executed_utc'],
        'run_manifest': run_path.relative_to(ROOT).as_posix(),
        'run_manifest_sha256': sha256(run_path),
        'source_sha256': source_sha256,
        'conditions': {
            'corner': 'typical',
            'temperature_C': design['temperature_C'],
            'supply_V': design['supply_V'],
            'input_common_V': design['input_common_V'],
            'statistical_global': 0,
            'statistical_mismatch': 0,
            'input_port': 'v_id = v_i1 - v_i2; AC 1 V with inputs +0.5/-0.5 V',
            'output_port': 'right single-ended v(o) / v_id, open loop',
            'frequency_Hz': design['frequency_Hz'],
            'points_per_decade': design['points_per_decade'],
            'phase_convention': 'atan2(v(o)) unwrapped in ascending frequency, degrees',
        },
        'target': design['target'],
        'groups': VISIBLE_CASES,
        'cases': cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = json.dumps(package(), ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'
    if args.check:
        if not OUT.is_file() or OUT.read_bytes() != content.encode('utf-8'):
            raise SystemExit('OTA frequency payload is stale; run scripts/export_ota_frequency.py')
        print('PASS: OTA candidate payload matches every hashed AC sweep and metrics record.')
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(content, encoding='utf-8', newline='\n')
        print(f'Exported {OUT.relative_to(ROOT)} with {len(CASE_DETAILS)} archived cases.')


if __name__ == '__main__':
    main()
