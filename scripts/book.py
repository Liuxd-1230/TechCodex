"""Build one reading site from the repository's original Markdown sources."""
import argparse
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, unquote, urlsplit, urlunsplit

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'build/book-source'
REPOSITORY_URL='https://github.com/Liuxd-1230/TechCodex'
IMAGE_SUFFIXES={'.svg','.png'}
MARKDOWN_LINK=re.compile(r'(!?\[[^\]]*\]\()([^)]+)(\))')
ROUTES={
    'README.md':'index.md',
    '模拟/README.md':'analog/index.md',
    '模拟/约定.md':'analog/conventions.md',
    '模拟/02-MOS器件.md':'analog/devices/index.md',
    '模拟/02-MOS器件/02-非理想效应.md':'analog/devices/nonideal.md',
    '模拟/02-MOS器件/03-小信号与电容.md':'analog/devices/small-signal.md',
    '模拟/03-单级放大器/README.md':'analog/stages/index.md',
    '模拟/03-单级放大器/01-分析方法.md':'analog/stages/analysis.md',
    '模拟/03-共源级.md':'analog/stages/common-source.md',
    '模拟/03-单级放大器/03-源跟随器.md':'analog/stages/source-follower.md',
    '模拟/03-单级放大器/04-共栅级.md':'analog/stages/common-gate.md',
    '模拟/03-单级放大器/05-共源共栅.md':'analog/stages/cascode.md',
    '模拟/04-差分放大器/README.md':'analog/differential/index.md',
    '模拟/04-差分放大器/01-电流如何分配.md':'analog/differential/current-steering.md',
    '模拟/04-差分放大器/02-对称性与差模增益.md':'analog/differential/symmetry.md',
    '模拟/04-差分放大器/03-共模与尾源.md':'analog/differential/common-mode.md',
    '模拟/04-差分放大器/04-余量与线性范围.md':'analog/differential/headroom.md',
    '模拟/04-差分放大器/05-MOS负载.md':'analog/differential/mos-loads.md',
    '模拟/04-差分放大器/06-Gilbert单元.md':'analog/differential/gilbert.md',
    '模拟/实验/差分对/README.md':'labs/differential.md',
    '模拟/05-电流镜与偏置/README.md':'analog/mirrors/index.md',
    '模拟/05-电流镜与偏置/01-普通电流镜.md':'analog/mirrors/basic.md',
    '模拟/05-电流镜与偏置/02-共源共栅镜.md':'analog/mirrors/cascode.md',
    '模拟/05-电流镜与偏置/03-有源镜与OTA.md':'analog/mirrors/active-load.md',
    '模拟/05-电流镜与偏置/04-偏置与启动.md':'analog/mirrors/biasing.md',
    '模拟/05-电流镜与偏置/05-设计一次电流源.md':'analog/mirrors/design.md',
    '模拟/实验/电流镜/README.md':'labs/mirrors.md',
    '模拟/06-频率响应/README.md':'analog/frequency/index.md',
    '模拟/06-频率响应/01-节点与极点.md':'analog/frequency/nodes.md',
    '模拟/06-频率响应/02-米勒与共源.md':'analog/frequency/miller.md',
    '模拟/06-频率响应/03-源跟随与共栅.md':'analog/frequency/follower-gate.md',
    '模拟/06-频率响应/04-共源共栅.md':'analog/frequency/cascode.md',
    '模拟/06-频率响应/05-差分结构.md':'analog/frequency/differential.md',
    '模拟/06-频率响应/06-OTA进入频域.md':'analog/frequency/ota.md',
    '模拟/06-频率响应/07-近似与设计判断.md':'analog/frequency/methods.md',
    '模拟/实验/频率响应/README.md':'labs/frequency.md',
    '模拟/07-噪声/README.md':'analog/noise/index.md',
    '模拟/07-噪声/01-统计与频谱.md':'analog/noise/statistics.md',
    '模拟/07-噪声/02-器件与表示.md':'analog/noise/sources.md',
    '模拟/07-噪声/03-单级放大器.md':'analog/noise/stages.md',
    '模拟/07-噪声/04-镜像差分与相关.md':'analog/noise/mirrors-differential.md',
    '模拟/07-噪声/05-带宽与积分.md':'analog/noise/bandwidth.md',
    '模拟/07-噪声/06-噪声预算与设计.md':'analog/noise/design.md',
    '模拟/实验/噪声/README.md':'labs/noise.md',
    '模拟/实验/README.md':'labs/index.md',
    'models/README.md':'labs/models.md',
    'docs/WINDOWS.md':'labs/windows.md',
    'docs/PLAN.md':'about/roadmap.md',
    'docs/SOURCES.md':'about/sources.md',
    'docs/VALIDATION.md':'about/validation-v1.md',
    'docs/第二版编辑说明.md':'about/edition2.md',
    'docs/知识覆盖.md':'about/curriculum.md',
    'docs/教例地图.md':'about/examples.md',
    'docs/网站维护.md':'about/site.md',
    'docs/第二版验收.md':'about/validation-v2.md',
}


def repository_url(original):
    """Return a stable GitHub source URL for a repository-relative path."""
    path=ROOT/Path(original)
    kind='tree' if path.is_dir() else 'blob'
    return f'{REPOSITORY_URL}/{kind}/main/{quote(original,safe="/")}'


def _local_destination(url,source):
    """Return the staged path for a routed page or local image, if any."""
    parts=urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path or parts.path.startswith('/'):
        return None,parts
    original=posixpath.normpath(posixpath.join(posixpath.dirname(source),unquote(parts.path)))
    if original in ROUTES:
        return ROUTES[original],parts
    if original.startswith('web/assets/'):
        return original.removeprefix('web/'),parts
    source_path=ROOT/Path(original)
    if Path(original).suffix.lower() in IMAGE_SUFFIXES and source_path.is_file():
        return original,parts
    return None,parts


def _rewrite_url(url,source,target):
    if url.startswith('#') or url.startswith('/'):
        return url
    destination,parts=_local_destination(url,source)
    if destination is None:
        if parts.scheme or parts.netloc or not parts.path:
            return url
        original=posixpath.normpath(posixpath.join(posixpath.dirname(source),unquote(parts.path)))
        base=repository_url(original)
    else:
        base=posixpath.relpath(destination,posixpath.dirname(target) or '.')
    return urlunsplit(('', '', base, parts.query, parts.fragment))


def rewrite_links(text,source,target):
    def replace_markdown(match):
        url=match.group(2)
        return match.group(1)+_rewrite_url(url,source,target)+match.group(3)
    return MARKDOWN_LINK.sub(replace_markdown,text)


def referenced_images(text,source):
    """Find local images referenced by ordinary Markdown links or images."""
    urls=(match.group(2) for match in MARKDOWN_LINK.finditer(text))
    images=set()
    for url in urls:
        destination,_=_local_destination(url,source)
        if destination and (destination in ROUTES.values() or destination.startswith('assets/')):
            continue
        if destination and Path(destination).suffix.lower() in IMAGE_SUFFIXES:
            images.add(destination)
    return images


SEARCH_EXCLUDED_ABOUT={'about/roadmap.md','about/validation-v1.md','about/edition2.md',
                       'about/site.md','about/validation-v2.md'}


def _page_metadata(target):
    if target not in SEARCH_EXCLUDED_ABOUT:
        return ''
    return '---\nsearch:\n  exclude: true\n---\n\n'


def prepare():
    # Only the generated stage may be removed; never follow a path outside build/.
    expected=(ROOT/'build').resolve()
    if STAGE.resolve().parent!=expected or STAGE.name!='book-source' or STAGE.is_symlink():
        raise RuntimeError('Unexpected staging location')
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    images=set()
    for original,target in ROUTES.items():
        source=ROOT/original
        if not source.is_file():
            raise FileNotFoundError(f'Mapped reading source is missing: {original}')
        dest=STAGE/target
        dest.parent.mkdir(parents=True,exist_ok=True)
        content=source.read_text(encoding='utf-8')
        images.update(referenced_images(content,original))
        content=rewrite_links(content,original,target)
        dest.write_text(_page_metadata(target)+content,encoding='utf-8',newline='\n')
    for original in sorted(images):
        source=ROOT/Path(original)
        dest=STAGE/Path(original)
        if not source.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError(f'Image reference escapes repository: {original}')
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,dest)
    shutil.copytree(ROOT/'web/assets',STAGE/'assets',dirs_exist_ok=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['build','preview','serve','deploy'])
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    prepare()
    base=[sys.executable,'-m','mkdocs']
    if args.command=='serve':
        command=base+['serve','--dev-addr',f'127.0.0.1:{args.port}']
    elif args.command=='deploy':
        command=base+['gh-deploy','--strict','--message','Publish reading edition from {sha}']
    else:
        command=base+['build']+([] if args.command=='preview' else ['--strict'])
    subprocess.run(command,cwd=ROOT,check=True)


if __name__=='__main__':
    main()
