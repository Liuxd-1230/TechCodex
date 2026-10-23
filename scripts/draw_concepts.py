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
<style>body{{margin:0;padding:16px;background:{C['paper']};color:{C['ink']};font-family:{SANS}}}.diagram-container{{max-width:420px;min-width:0;margin:auto;overflow-x:auto}}svg{{display:block;width:100%;min-width:320px}}svg text{{font-family:{SANS}}}@media print{{.diagram-container{{overflow:visible}}svg{{min-width:0}}}}</style></head><body><main class="diagram-container">
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
    b = text(160,24,'输入抬高后',18,weight=600)
    b += text(160,48,'什么让输出停下来？',18,weight=600)
    # Causal arrows are explanatory relationships, not electrical wires.
    b += f'<g fill="none" stroke="{C["muted"]}" stroke-width="1.4" marker-end="url(#arrow)"><path d="M184 132V172"/><path d="M184 236V276"/><path d="M184 340V380"/></g>'
    b += f'<path d="M72 412H32Q24 412 24 404V108Q24 100 32 100H70" fill="none" stroke="{C["accent"]}" stroke-width="1.4" stroke-dasharray="5 4" marker-end="url(#arrow-accent)"/>'
    nodes=[(68,'vgs = vi − vo','输入阶跃，vo 起初不变'),(172,'沟道电流增加','ΔiD ≈ gm Δvgs'),(276,'净电流给输出电容充电','偏置源仍取原来的电流'),(380,'源极输出 vo 上升','反过来减小 Δvgs')]
    for n,(y,label,sub) in enumerate(nodes):
        b += rect(72,y,224,64,'accent-tint' if n==3 else 'paper','accent' if n==3 else 'muted',6)
        b += text(184,y+27,label,16,weight=600)+text(184,y+49,sub,13,'muted')
    b += text(160,488,'输入固定后：推动电流逐渐减小',15,'accent',weight=600)
    b += text(160,516,'直到流入与流出重新平衡',15)
    b += f'<line x1="24" y1="544" x2="296" y2="544" stroke="{C["rule"]}"/>'
    b += text(24,572,'实线：最初的因果方向',13,'muted','start')
    b += text(24,596,'虚线：输出对栅源电压的反作用',13,'muted','start')
    b += text(24,624,'饱和区小扰动；暂忽略体效应与 ro',13,'muted','start')
    return page('sf-feedback','源跟随器的局部纠偏路径','栅源电压增量增加沟道电流，净电流给输出电容充电，源极抬高又减小栅源电压增量，直至电流重新平衡。',644,b)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir',type=Path,required=True)
    args=parser.parse_args()
    C=tokens()
    for slug,html in [('mos-charge',mos()),('sf-feedback',follower())]:
        src=SOURCE/f'{slug}.html'
        src.write_text(html,encoding='utf-8')
        subprocess.run([sys.executable,str(args.skill_dir/'scripts/self_check.py'),'--offline',str(src)],check=True)
        subprocess.run([sys.executable,str(args.skill_dir/'scripts/export_svg.py'),str(src),str(OUTPUT/f'{slug}.svg'),'--system-fonts'],check=True)
