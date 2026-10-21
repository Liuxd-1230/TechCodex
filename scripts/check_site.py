"""Check generated local links, assets, figures and self-hosted math runtime."""
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
errors = []
documents = {p: BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
             for p in SITE.rglob('*.html')}
checked = 0
for path, soup in documents.items():
    for element in soup.select('[href], [src]'):
        value = element.get('href') or element.get('src')
        url = urlsplit(value)
        if url.scheme or url.netloc or not value:
            continue
        target = unquote(url.path)
        if target.startswith('/TechCodex/'):
            dest = SITE / target.removeprefix('/TechCodex/')
        elif target.startswith('/'):
            dest = SITE / target.lstrip('/')
        elif not target:
            dest = path
        else:
            dest = path.parent / target
        dest = dest.resolve()
        if dest.is_dir():
            dest /= 'index.html'
        checked += 1
        if not dest.is_file():
            errors.append(f'{path.relative_to(SITE)}: missing {value}')
        elif url.fragment and dest in documents:
            if not documents[dest].find(id=unquote(url.fragment)):
                errors.append(f'{path.relative_to(SITE)}: missing anchor {value}')
    for figure in soup.select('article figure'):
        if not figure.find('figcaption') or not figure.find('img', alt=True):
            errors.append(f'{path.relative_to(SITE)}: figure missing caption/alt')

for route in ('analog/stages/common-source', 'analog/devices/small-signal'):
    soup = documents[SITE / route / 'index.html']
    if not soup.select('details .arithmatex'):
        errors.append(f'{route}: expandable derivation was not parsed')
sample = documents[SITE / 'analog/stages/source-follower/index.html']
if sample.select_one('details strong') is None:
    errors.append('Sample exercise Markdown was not parsed')

vendor = ROOT / 'web/assets/vendor/mathjax'
manifest = json.loads((vendor / 'source.json').read_text(encoding='utf-8'))
for name, expected in manifest['files'].items():
    if hashlib.sha256((vendor / name).read_bytes()).hexdigest() != expected:
        errors.append(f'MathJax source hash mismatch: {name}')
    if (SITE / 'assets/vendor/mathjax' / name).read_bytes() != (vendor / name).read_bytes():
        errors.append(f'MathJax deployment copy mismatch: {name}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(documents)} HTML pages, {checked} local references, '
      f'figure semantics, expandable math and {len(manifest["files"])} MathJax files.')
