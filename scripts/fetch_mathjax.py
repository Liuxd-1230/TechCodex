"""Restore the pinned, self-hosted MathJax package and its local CHTML fonts."""
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'web/assets/vendor/mathjax'
lock=json.loads((DEST/'source.json').read_text(encoding='utf-8'))
url=f"https://registry.npmjs.org/mathjax/-/mathjax-{lock['version']}.tgz"
data=urllib.request.urlopen(url,timeout=60).read()
digest='sha512-'+base64.b64encode(hashlib.sha512(data).digest()).decode()
if digest!=lock['integrity']:
    raise RuntimeError('MathJax package checksum mismatch')
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
    for member in archive.getmembers():
        name=member.name
        if name=='package/LICENSE':relative='LICENSE'
        elif name=='package/es5/tex-chtml-full.js':relative='tex-chtml-full.js'
        elif re.fullmatch(r'package/es5/output/chtml/fonts/woff-v2/[\w-]+\.woff',name):
            relative=name.removeprefix('package/es5/')
        else:continue
        target=DEST/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(archive.extractfile(member).read())
lock['renderer']='CHTML; fonts self-hosted'
lock['files']={p.relative_to(DEST).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='source.json' and p.name!='tex-svg-full.js'}
(DEST/'source.json').write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
print(f"Verified MathJax {lock['version']}; restored {len(lock['files'])} runtime/license files")
