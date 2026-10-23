"""Build one reading site from the repository's original Markdown sources."""
import argparse
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'build/book-source'
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
    '模拟/实验/README.md':'labs/index.md',
    'models/README.md':'labs/models.md',
    'docs/WINDOWS.md':'labs/windows.md',
    'docs/PLAN.md':'about/roadmap.md',
    'docs/SOURCES.md':'about/sources.md',
    'docs/VALIDATION.md':'about/validation-v1.md',
    'docs/第二版编辑说明.md':'about/edition2.md',
    'docs/知识覆盖.md':'about/curriculum.md',
    'docs/网站维护.md':'about/site.md',
    'docs/第二版验收.md':'about/validation-v2.md',
}


def rewrite_links(text,source,target):
    def replace(match):
        url=match.group(2)
        if re.match(r'^[a-zA-Z][\w+.-]*:',url) or url.startswith(('#','/')):
            return match.group(0)
        path,sep,fragment=url.partition('#')
        original=posixpath.normpath(posixpath.join(posixpath.dirname(source),unquote(path)))
        destination=ROUTES.get(original,original)
        if original.startswith('web/assets/'):
            destination=original.removeprefix('web/')
        relative=posixpath.relpath(destination,posixpath.dirname(target) or '.')
        return match.group(1)+relative+(sep+fragment if sep else '')+')'
    return re.sub(r'(!?\[[^\]]*\]\()([^)]+)\)',replace,text)


def prepare():
    # Only the generated stage may be removed; never follow a path outside build/.
    expected=(ROOT/'build').resolve()
    if STAGE.resolve().parent!=expected or STAGE.name!='book-source' or STAGE.is_symlink():
        raise RuntimeError('Unexpected staging location')
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    sources=[ROOT/'README.md',ROOT/'LICENSE',ROOT/'requirements.txt',ROOT/'requirements-lock.txt']
    for directory in ('模拟','docs','models','scripts'):
        sources.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and
                       '__pycache__' not in p.parts and not p.name.endswith(('.pyc','.lint.txt')) and '__on_page' not in p.name)
    for source in sources:
        original=source.relative_to(ROOT).as_posix()
        target=ROUTES.get(original,original)
        dest=STAGE/target
        dest.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix=='.md':
            content=rewrite_links(source.read_text(encoding='utf-8'),original,target)
            dest.write_text(content,encoding='utf-8',newline='\n')
        else:
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
