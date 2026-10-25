"""Check generated local links, assets, figures and self-hosted math runtime."""
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from export_steering_demo import package, OUT
from export_mirror_demo import package as mirror_package, OUT as MIRROR_OUT
from book import ROUTES, SEARCH_EXCLUDED_ABOUT, assert_public_asset

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
errors = []
documents = {p: BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
             for p in SITE.rglob('*.html')}
checked = 0

def output_for_route(route):
    source = Path(route)
    if source.name == 'index.md':
        return SITE / source.parent / 'index.html'
    return SITE / source.with_suffix('') / 'index.html'

for route in ROUTES.values():
    if not output_for_route(route).is_file():
        errors.append(f'Mapped reading route missing from site: {route}')

for suffix in ('.csv', '.py', '.cir', '.ngspice', '.spice', '.lib'):
    if any(SITE.rglob(f'*{suffix}')):
        errors.append(f'Unpublished source artifact found in site: *{suffix}')
for directory in ('models', 'scripts'):
    if (SITE / directory).exists():
        errors.append(f'Repository source directory leaked into site: {directory}')
for name in ('LICENSE', 'requirements.txt', 'requirements-lock.txt', 'pyproject.toml', 'uv.lock'):
    if (SITE / name).exists():
        errors.append(f'Repository root file leaked into site: {name}')

for asset in SITE.rglob('*'):
    if asset.is_file():
        try:
            assert_public_asset(asset)
        except RuntimeError as exc:
            errors.append(str(exc))

search_index_path = SITE / 'search/search_index.json'
if not search_index_path.is_file():
    errors.append('Search index is missing')
else:
    search_locations = {entry.get('location', '').split('#', 1)[0].strip('/')
                        for entry in json.loads(search_index_path.read_text(encoding='utf-8')).get('docs', [])}
    for route in SEARCH_EXCLUDED_ABOUT:
        location = route.removesuffix('.md').removeprefix('about/')
        if f'about/{location}' in search_locations:
            errors.append(f'Management page was included in search: {route}')

for path, soup in documents.items():
    math_script=soup.find('script',src=lambda value:value and 'tex-chtml-full.js' in value)
    if bool(soup.select('.arithmatex')) != bool(math_script):
        errors.append(f'{path.relative_to(SITE)}: math runtime must match actual math content')
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

# These checks cover injected, executable modules, not merely asset existence.
for name,route,module,fallback,control_count in (
    ('mos-channel','analog/devices','mos-channel.js','mos-channel.svg',2),
    ('differential-modes','analog/differential/common-mode','differential-modes.js','diff-modes.svg',3),
    ('ota-frequency','analog/frequency/ota','ota-frequency.js','frequency-ota-load.svg',2),
):
    page=documents[SITE/route/'index.html']
    demo=page.select_one(f'[data-demo="{name}"]')
    if demo is None or not demo.has_attr('hidden'):
        errors.append(f'{name}: progressive enhancement root missing')
        continue
    if not page.select_one(f'script[type="module"][src*="/{module}"]'):
        errors.append(f'{name}: executable module was not injected')
    if len(demo.select('input,select'))!=control_count:
        errors.append(f'{name}: controls missing')
    for control in demo.select('input,select'):
        if not demo.find('label',attrs={'for':control.get('id')}):
            errors.append(f'{name}: control lacks label')
    if not demo.select_one('[role="status"]') or '{{' in str(demo):
        errors.append(f'{name}: observation or resolved template missing')
    for svg in demo.select('svg'):
        if not svg.find('title') or not svg.find('desc'):
            errors.append(f'{name}: SVG lacks accessible description')
    if not page.select_one(f'figure img[src*="{fallback}"]'):
        errors.append(f'{name}: static reading fallback missing')

if (SITE/'assets/demos/ota-frequency-data.json').read_bytes()!=(ROOT/'web/assets/demos/ota-frequency-data.json').read_bytes():
    errors.append('OTA frequency payload differs from the published copy')
if (SITE/'about/examples').exists() or any(s.select_one('nav a[href*="about/examples"]') for s in documents.values()):
    errors.append('Source-only example map leaked into reader routes/navigation')
for route,names in (
    ('analog/devices/nonideal',('device-body-port','device-body-evidence','device-output-slope')),
    ('analog/frequency/differential',('frequency-mirror-phasors','frequency-mirror-nodes')),
):
    page=documents[SITE/route/'index.html']
    for name in names:
        figure=page.select_one(f'#figure-{name}')
        if not figure or not figure.select_one(f'img[alt][src*="{name}.svg"]') or not figure.find('figcaption'):
            errors.append(f'{route}: static teaching figure/caption missing: {name}')
if not documents[SITE/'analog/frequency/differential/index.html'].select_one('#figure-frequency-ota .diagram-viewport[tabindex="0"][role="region"]'):
    errors.append('OTA complete schematic lacks its keyboard-accessible local reading viewport')
sample = documents[SITE / 'analog/stages/source-follower/index.html']
if sample.select_one('details strong') is None:
    errors.append('Sample exercise Markdown was not parsed')

expected_payload = package().encode('utf-8')
if OUT.read_bytes() != expected_payload or (SITE / 'assets/demos/steering-data.json').read_bytes() != expected_payload:
    errors.append('Interactive GF180 payload is stale or does not match the deployed copy')

demo_page = documents[SITE / 'analog/differential/current-steering/index.html']
demo = demo_page.select_one('[data-demo="current-steering"]')
if demo is None or not demo.has_attr('hidden'):
    errors.append('Demo must start hidden and enhance only after successful initialization')
else:
    if len(demo.select('input[type="range"]')) != 2:
        errors.append('Demo voltage/bias controls missing')
    for control in demo.select('input'):
        if control.get('type') == 'range' and not demo.find('label', attrs={'for': control.get('id')}):
            errors.append('Demo control has no accessible label')
    for svg in demo.select('svg'):
        if not svg.find('title') or not svg.find('desc'):
            errors.append('Demo SVG lacks title/description')
    if not demo.select_one('[role="status"]'):
        errors.append('Demo lacks accessible observation text')
    if not demo_page.select_one('figure img[src*="diff-steering.svg"]'):
        errors.append('Static current-steering fallback missing')
    if '{{' in str(demo):
        errors.append('Demo asset URL placeholders were not resolved')

follower_page=documents[SITE/'analog/stages/source-follower/index.html']
follower=follower_page.select_one('[data-demo="source-follower"]')
if follower is None or not follower.has_attr('hidden'):
    errors.append('Source follower must enhance progressively')
else:
    for control in follower.select('input,select'):
        if not follower.find('label',attrs={'for':control.get('id')}):
            errors.append('Source follower control lacks label')
    for svg in follower.select('svg[role="img"]'):
        if not svg.find('title') or not svg.find('desc'):
            errors.append('Source follower diagram lacks description')
    if not follower.select_one('[role="status"]') or '{{' in str(follower):
        errors.append('Source follower status/template incomplete')
    if not follower_page.select_one('#figure-sf-feedback img'):
        errors.append('Source follower static circuit fallback missing')
    if len(follower_page.select('.sf-loading-pair figure'))!=2:
        errors.append('Source follower port comparison missing')

miller_page=documents[SITE/'analog/frequency/miller/index.html']
miller=miller_page.select_one('[data-demo="miller-poles"]')
if miller is None or not miller.has_attr('hidden'):
    errors.append('Miller demo must enhance progressively')
else:
    for control in miller.select('input[type="range"]'):
        if not miller.find('label',attrs={'for':control.get('id')}):errors.append('Miller range lacks label')
    if len(miller.select('input[type="range"]'))!=2:errors.append('Miller controls missing')
    for svg in miller.select('svg'):
        if not svg.find('title') or not svg.find('desc'):errors.append('Miller SVG lacks accessible description')
    if '{{' in str(miller):errors.append('Miller template unresolved')
    if not miller_page.select_one('figure img[src*="frequency-miller-response.svg"]'):errors.append('Miller static fallback missing')
    if not miller.select_one('[role="status"]'):errors.append('Miller lacks live observation')
from build_noise_demo import package as noise_package,OUT as NOISE_OUT
expected_noise=noise_package().encode('utf-8')
if NOISE_OUT.read_bytes()!=expected_noise or (SITE/'assets/demos/noise-data.json').read_bytes()!=expected_noise:
    errors.append('Noise payload is stale or deployment differs')
noise_page=documents[SITE/'analog/noise/bandwidth/index.html']
noise=noise_page.select_one('[data-demo="noise-band"]')
if noise is None or not noise.has_attr('hidden'):
    errors.append('Noise must enhance progressively')
else:
    if len(noise.select('input[type="range"]'))!=2:errors.append('Noise band controls missing')
    for control in noise.select('input,select'):
        if not noise.find('label',attrs={'for':control.get('id')}):errors.append('Noise control lacks label')
    for svg in noise.select('svg'):
        if not svg.find('title') or not svg.find('desc'):errors.append('Noise SVG lacks accessible description')
    if not noise.select_one('[role="status"]') or '{{' in str(noise):errors.append('Noise status/template incomplete')
    if not noise_page.select_one('figure img[src*="noise-band.svg"]'):errors.append('Noise static fallback missing')
for route in ('statistics','sources','stages','mirrors-differential','bandwidth','design'):
    page=documents[SITE/'analog/noise'/route/'index.html']
    if not page.select('.arithmatex'):errors.append('Noise math missing: '+route)
if (SITE/'PRODUCT.md').exists() or (SITE/'DESIGN.md').exists() or (SITE/'.impeccable').exists():
    errors.append('Internal design instructions must never be published')
vendor = ROOT / 'web/assets/vendor/mathjax'
mirror_expected=mirror_package().encode('utf-8')
if MIRROR_OUT.read_bytes()!=mirror_expected or (SITE/'assets/demos/mirror-data.json').read_bytes()!=mirror_expected:
    errors.append('Mirror payload stale or deployment copy differs')
mirror_page=documents[SITE/'analog/mirrors/cascode/index.html']
mirror_demo=mirror_page.select_one('[data-demo="mirror-compliance"]')
if mirror_demo is None or not mirror_demo.has_attr('hidden'):
    errors.append('Mirror must enhance progressively')
else:
    for svg in mirror_demo.select('svg'):
        if not svg.find('title') or not svg.find('desc'):errors.append('Mirror SVG lacks accessible description')
    if len(mirror_demo.select('[data-topology]'))!=2:errors.append('Mirror topologies missing')
    if not mirror_demo.find('label',attrs={'for':'mirror-voltage'}):errors.append('Mirror slider label missing')
    if not mirror_page.select_one('figure img[src*="mirror-compliance.svg"]'):errors.append('Static mirror fallback missing')

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
