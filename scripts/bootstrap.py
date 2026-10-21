"""Install a pinned, portable Windows ngspice locally; never change global PATH."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://downloads.sourceforge.net/project/ngspice/ng-spice-rework/47/ngspice-47_64.7z'
SHA256 = '59225971bd68cdd1199443649aa4615a9e6d684933f205ab49006a3942518f5a'


def verify_models():
    lock = json.loads((ROOT / 'models/manifest.json').read_text(encoding='utf-8'))
    for name, digest in lock['files'].items():
        actual = hashlib.sha256((ROOT / 'models/gf180mcu' / name).read_bytes()).hexdigest()
        if actual != digest:
            raise RuntimeError(f'Model checksum mismatch: {name}')
    return lock


def simulator():
    override = os.environ.get('NGSPICE')
    if override:
        path = Path(override).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError('NGSPICE must point to an executable file')
        return str(path)
    local = ROOT / '.tools/Spice64/bin/ngspice_con.exe'
    if local.is_file():
        return str(local)
    found = shutil.which('ngspice_con') or shutil.which('ngspice')
    if found:
        return found
    raise FileNotFoundError('Run python scripts/bootstrap.py, or set NGSPICE to a native executable')


def main():
    verify_models()
    try:
        print(f'ngspice: {simulator()}')
        return
    except FileNotFoundError:
        pass
    if platform.system() != 'Windows':
        raise SystemExit('Install native ngspice with your package manager, then set NGSPICE if needed.')
    import py7zr
    cache = ROOT / '.cache'
    cache.mkdir(exist_ok=True)
    archive = cache / 'ngspice-47_64.7z'
    if not archive.exists():
        print('Downloading official Windows ngspice 47 archive...')
        urllib.request.urlretrieve(URL, archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError('Archive checksum mismatch; keep the file for inspection, do not execute')
    target = ROOT / '.tools'
    target.mkdir(exist_ok=True)
    with py7zr.SevenZipFile(archive) as bundle:
        # Only permit members inside the installation directory.
        for name in bundle.getnames():
            resolved = (target / name).resolve()
            if not resolved.is_relative_to(target.resolve()):
                raise RuntimeError(f'Unsafe archive member: {name}')
        bundle.extractall(target)
    print(f'ngspice: {simulator()}')


if __name__ == '__main__':
    main()
