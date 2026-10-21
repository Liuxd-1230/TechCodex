"""Recover vendored upstream files byte for byte from the locked commit."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
lock = json.loads((ROOT / 'models/manifest.json').read_text(encoding='utf-8'))
for name, digest in lock['files'].items():
    source = name if name == 'LICENSE' else 'models/ngspice/' + name
    url = f"https://raw.githubusercontent.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr/{lock['commit']}/{source}"
    data = urllib.request.urlopen(url, timeout=60).read()
    if hashlib.sha256(data).hexdigest() != digest:
        raise RuntimeError(f'Upstream checksum mismatch: {name}')
    target = ROOT / 'models/gf180mcu' / name
    if target.exists() and target.read_bytes() != data:
        raise RuntimeError(f'Refusing to overwrite modified model: {target.name}')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(f'Verified {name}')
