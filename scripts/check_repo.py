"""Check local Markdown links, SVG validity, provenance and model integrity."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from bootstrap import ROOT, verify_models


def main():
    verify_models()
    files=[p for p in ROOT.rglob('*') if p.is_file() and not any(
        x in ('.git','.tools','.venv','.venv-site','.cache','build','site','node_modules','__pycache__') for x in p.relative_to(ROOT).parts)]
    links=0
    for file in files:
        if file.suffix=='.md':
            s=file.read_text(encoding='utf-8')
            if s.count('```')%2 or s.count('$$')%2:
                raise AssertionError(f'Unbalanced fence/math block: {file.relative_to(ROOT)}')
            for url in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',s):
                if re.match(r'\w+://',url) or url.startswith('#'):
                    continue
                path=unquote(url.split('#')[0])
                if not (file.parent/path).exists():
                    raise AssertionError(f'Broken link: {file.relative_to(ROOT)} -> {url}')
                links+=1
        if file.suffix=='.svg':
            ET.parse(file)
        if file.suffix in ('.md','.py','.json','.cir'):
            s=file.read_text(encoding='utf-8')
            bad_pattern=r'(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|C:\\Users\\|'+('/opt/'+'local/')+')'
            if re.search(bad_pattern,s):
                raise AssertionError(f'Possible credential or personal path: {file.relative_to(ROOT)}')
    record=json.loads((ROOT/'模拟/实验/data/run.json').read_text(encoding='utf-8'))
    for name,digest in record['netlist_sha256'].items():
        if hashlib.sha256((ROOT/'模拟/实验'/name).read_bytes()).hexdigest()!=digest:
            raise AssertionError(f'Simulation predates netlist changes: {name}')
    if hashlib.sha256((ROOT/'scripts/run.py').read_bytes()).hexdigest()!=record['runner_sha256']:
        raise AssertionError('Simulation predates runner changes')
    for name,digest in record['data_sha256'].items():
        if hashlib.sha256((ROOT/'模拟/实验/data'/name).read_bytes()).hexdigest()!=digest:
            raise AssertionError(f'Data changed since simulation: {name}')
    differential=ROOT/'模拟/实验/差分对/data/run.json'
    if differential.exists():
        diff_record=json.loads(differential.read_text(encoding='utf-8'))
        for name,digest in diff_record['sha256'].items():
            path=(ROOT/name).resolve()
            if not path.is_relative_to(ROOT.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise AssertionError(f'Chapter 4 artifact changed since simulation: {name}')
    mirror_record=ROOT/'模拟/实验/电流镜/data/run.json'
    if mirror_record.exists():
        for name,digest in json.loads(mirror_record.read_text(encoding='utf-8'))['sha256'].items():
            path=(ROOT/name).resolve()
            if not path.is_relative_to(ROOT.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise AssertionError(f'Chapter 5 artifact changed since simulation: {name}')
    print(f'PASS: {links} local links; all SVG XML; Markdown fences; model/netlist hashes; path/credential scan')


if __name__=='__main__':
    main()
