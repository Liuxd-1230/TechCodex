"""Diagram Design teaching figures: HTML sources, then portable SVG exports.

The project profile is versioned in web/diagrams; the installed skill is never
modified. Run with --skill-dir pointing to a local diagram-design installation.
"""
from pathlib import Path
import argparse
import re
import subprocess
import sys
from html import escape

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'web/diagrams'
OUTPUT = ROOT / '模拟/图'
SANS = '"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif'


def tokens():
    guide = (SOURCE / 'techcodex.md').read_text(encoding='utf-8')
    return dict(re.findall(r'^\| `([\w-]+)` \|[^\n]*?\| `(#[0-9a-fA-F]{6})`', guide, re.M))


def text(x, y, label, size=16, color='ink', anchor='middle', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{C[color]}" text-anchor="{anchor}" font-weight="{weight}">{escape(label)}</text>'


def rect(x, y, w, h, fill='paper', stroke='muted', radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{C[fill]}" stroke="{C[stroke]}"/>'


def page(slug, title, desc, height, body):
    markers = ''.join(f'<marker id="{name}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="{C[color]}"/></marker>' for name, color in [('arrow','muted'),('arrow-accent','accent'),('arrow-link','link')])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{margin:0;padding:16px;background:{C['paper']};color:{C['ink']};font-family:{SANS}}}.diagram-container{{max-width:420px;min-width:0;margin:auto;overflow-x:auto}}svg{{display:block;width:100%;min-width:320px}}svg text{{font-family:{SANS};stroke:none}}@media print{{.diagram-container{{overflow:visible}}svg{{min-width:0}}}}</style></head><body><main class="diagram-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 {height}" role="img" aria-labelledby="{slug}-title {slug}-desc">
<title id="{slug}-title">{title}</title><desc id="{slug}-desc">{desc}</desc><defs>{markers}</defs>
<rect width="320" height="{height}" fill="{C['paper']}"/>
{body}
</svg></main></body></html>'''


def mos():
    # A local conceptual slice under the gate, not a manufacturing cross-section.
    b = text(160, 28, '从耗尽到反型', 20, weight=600)
    for y, inversion in [(72,False),(352,True)]:
        b += text(24, y, '反型：电子层出现' if inversion else '耗尽：空穴被排斥', 17, 'accent' if inversion else 'ink', 'start', 600)
        b += rect(48,y+20,224,36,'paper-2') + text(160,y+44,'G：更高的正栅压' if inversion else 'G：正栅压',15)
        b += rect(48,y+56,224,28) + text(160,y+76,'绝缘氧化层',14,'muted')
        if inversion:
            b += rect(48,y+84,224,28,'accent-tint','accent') + text(160,y+104,'e−   e−   e−   e−   e−',15,'accent')
            top=y+112
        else:
            top=y+84
        b += rect(48,top,224,56,'paper-2') + text(160,top+23,'A−   A−   A−   A−',15,'muted') + text(160,top+45,'耗尽区：固定受主离子',14,'muted')
        b += rect(48,top+56,224,36) + text(160,top+80,'p 型体区 · B = 0',15)
    b += '<path d="M160 268V316" fill="none" stroke="'+C['muted']+'" marker-end="url(#arrow)"/>'
    b += rect(176,280,112,24,'paper','paper',2) + text(180,298,'继续升高 VG',14,'muted','start')
    b += '<path d="M24 100V200M24 380V508" stroke="'+C['accent']+'" marker-end="url(#arrow-accent)"/>'
    b += f'<line x1="24" y1="592" x2="296" y2="592" stroke="{C["rule"]}"/>'
    b += text(24,620,'箭头：栅指向体区的电场分量',13,'muted','start')
    b += text(24,644,'概念分层 · 不按物理尺寸比例',13,'muted','start')
    b += text(24,668,'源、漏与接触在图外；VDS ≈ 0',13,'muted','start')
    return page('mos-charge','从耗尽到反型','正栅压排斥空穴，留下固定受主电荷；继续升高栅压后，表面形成可移动的电子反型层。',688,b)


def follower():
    # Reuse the same four-terminal electrical vocabulary as the book. Diagram
    # Design governs the causal annotation; the wires remain real circuit nets.
    from circuit_art import Canvas
    c=Canvas('源跟随器的充电与反作用',320,504)
    m=c.mos(100,164,'M1')
    c.line(130,64,*m['d']);c.text(130,52,'VDD',16,anchor='middle')
    c.text(24,140,'vi ↑',17,color=C['accent'])
    c.wire(m['b'],(210,164),(210,200),color='#a46723');c.ground(210,200,'#a46723')
    c.line(*m['s'],130,248);c.node(130,248)
    c.wire((130,248),(248,248),(248,264));c.cap(248,264);c.ground(248,324)
    c.text(268,300,'CL',15);c.text(248,234,'vo ↑',17,color=C['accent'],anchor='middle')
    c.line(130,248,130,276);c.current(130,276);c.ground(130,360);c.text(166,323,'IB 不变',15)
    c.arrow((162,94),(162,128),C['accent']);c.text(182,104,'iD 增加',15,color=C['accent'])
    c.arrow((164,236),(218,236),C['link'])
    c.text(24,426,'多出的电流流进 CL，输出升高。',15)
    c.text(24,454,'vo ↑ → vgs = vi − vo 减小',15,color=C['accent'])
    c.text(24,486,'直到 iD 回到 IB，净充电电流为零。',14)
    b=text(160,26,'电流怎样把源极抬高？',17,weight=600)
    b+=f'<g fill="none" stroke="{C["ink"]}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'+''.join(c.parts)+'</g>'
    return page('sf-feedback','源跟随器的充电与反作用','NMOS 源极连接偏置电流源与输出电容，输入抬高使多出的漏电流给电容充电，源极升高又减小栅源电压增量。',504,b)


def noise_referral():
    # Architecture layout: two parallel transfer maps, never a signal/PSD sum.
    b=text(160,28,'同一输出端口，分开计算',19,weight=600)
    for x in (80,240):
        b+=f'<path d="M{x} 100V144M{x} 208V252" fill="none" stroke="{C["muted"]}" marker-end="url(#arrow)"/>'
    for x in (24,184):
        b+=rect(x,144,112,64,'paper','ink',4)
    b+=text(80,70,'信号 vi',17)+text(240,70,'内部噪声 nk',16)
    b+=text(80,184,'Av(f)',20)+text(240,184,'Hk(f)',20)
    b+=text(80,280,'vo,s',20)+text(240,280,'vo,nk',20)
    b+=text(24,324,'信号幅值：vo,s = Av·vi',17,'ink','start')
    b+=text(24,360,'噪声 PSD：Sv,o = Σ |Hk|²Sk',16,'ink','start')
    b+=text(24,390,'上式对不相关源求和。',14,'muted','start')
    b+=rect(24,424,272,96,'accent-tint','accent',4)
    b+=text(160,452,'折回同一个信号输入端口',16,'accent')
    b+=text(160,488,'Sv,in = Sv,o / |Av|²',20,'accent')
    b+=f'<line x1="24" y1="544" x2="296" y2="544" stroke="{C["rule"]}"/>'
    b+=text(24,573,'箭头表示传递关系，不是电路导线。',14,'muted','start')
    b+=text(24,600,'同源多路径先合并 H，再求模平方。',14,'muted','start')
    return page('noise-referral','信号与噪声的输入参考','确定性输入经信号增益产生输出信号，内部噪声经各自路径产生输出噪声；二者分开计算，再用信号增益的模平方定义输入参考噪声。',624,b)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir',type=Path,required=True)
    args=parser.parse_args()
    C=tokens()
    for slug,html in [('mos-charge',mos()),('sf-feedback',follower()),('noise-referral',noise_referral())]:
        src=SOURCE/f'{slug}.html'
        src.write_text(html,encoding='utf-8')
        subprocess.run([sys.executable,str(args.skill_dir/'scripts/self_check.py'),'--offline',str(src)],check=True)
        subprocess.run([sys.executable,str(args.skill_dir/'scripts/export_svg.py'),str(src),str(OUTPUT/f'{slug}.svg'),'--system-fonts'],check=True)
