"""Turn native Markdown image/caption pairs into semantic textbook figures."""
from bs4 import BeautifulSoup
from pathlib import Path
import sys
from urllib.parse import quote
from mkdocs.utils import get_relative_url

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from book import ROUTES


def on_page_markdown(markdown,page,config,files):
    original=next((src for src,dest in ROUTES.items() if dest==page.file.src_uri),page.file.src_uri)
    page.edit_url='https://github.com/Liuxd-1230/TechCodex/blob/main/'+quote(original,safe='/')
    # GitHub understands Markdown inside native details. Python-Markdown needs
    # an explicit opt-in, added only while rendering the site.
    return markdown.replace('<details>','<details markdown="1">')


def on_page_content(html,page,config,files):
    marker='<!-- interactive: miller-poles -->'
    if marker in html:
        template=(Path(__file__).parent/'demos/miller-poles.html').read_text(encoding='utf-8')
        schematic=BeautifulSoup((Path(__file__).resolve().parents[1]/'模拟/图/frequency-cs-small.svg').read_text(encoding='utf-8'),'html.parser')
        for style in schematic.select('style'):style.decompose()
        for label in schematic.select('text'):
            key={'vin → RS → vg':'gate','vo':'output','Cf = Cgd':'capLabel'}.get(label.get_text())
            if key:label['data-frequency']=key
            if float(label.get('y',0))>=300:label.decompose()
        # html.parser lowercases SVG attributes; update the existing key rather
        # than serializing two differently-cased viewBox attributes.
        schematic.svg['viewbox']='0 0 680 270';schematic.svg['height']='270'
        schematic.svg.title['id']='miller-schematic-title';schematic.svg.desc['id']='miller-schematic-desc'
        schematic.svg['aria-labelledby']='miller-schematic-title miller-schematic-desc'
        template=template.replace('{{schematic}}',str(schematic.svg))
        for key,target in {'lab':'labs/frequency/','module':'assets/demos/miller-poles.js'}.items():
            template=template.replace('{{'+key+'}}',get_relative_url(target,page.url))
        html=html.replace(marker,template)
    # Only this explicit marker opts a chapter into a demo. Native Markdown keeps
    # its ordinary static diagrams; JS or data failures never remove that text.
    marker='<!-- interactive: differential-steering -->'
    if marker in html:
        template=(Path(__file__).parent/'demos/current-steering.html').read_text(encoding='utf-8')
        targets={
            'lab':'labs/differential/',
            'csv':'模拟/实验/差分对/data/ideal-steering-sweep.csv',
            'payload':'assets/demos/steering-data.json',
            'module':'assets/demos/current-steering.js',
        }
        for key,target in targets.items():
            template=template.replace('{{'+key+'}}',get_relative_url(target,page.url))
        html=html.replace(marker,template)
    marker='<!-- interactive: mirror-compliance -->'
    if marker in html:
        template=(Path(__file__).parent/'demos/mirror-compliance.html').read_text(encoding='utf-8')
        drawings=[]
        for name,art in [('medium','mirror-basic'),('cascode','mirror-cascode')]:
            drawing=BeautifulSoup((Path(__file__).resolve().parents[1]/'模拟/图'/f'{art}.svg').read_text(encoding='utf-8'),'html.parser')
            svg=drawing.svg
            svg['data-topology']=name
            if name=='cascode':svg['hidden']='hidden'
            for style in svg.select('style'):style.decompose()
            svg.title['id']=f'mirror-{name}-title';svg.desc['id']=f'mirror-{name}-desc'
            svg['aria-labelledby']=f'mirror-{name}-title mirror-{name}-desc'
            for label in svg.select('text'):
                if label.get_text()=='VB':label['data-mirror-node']='gate';label['font-size']='17'
            for key,x,y,anchor in [('output',480,48,'end')]+([('internal',495,378,'start')] if name=='cascode' else []):
                label=drawing.new_tag('text',attrs={'x':x,'y':y,'font-size':17,'fill':'#126e63','text-anchor':anchor,'data-mirror-node':key})
                svg.append(label)
            drawings.append(str(svg))
        template=template.replace('{{schematics}}',''.join(drawings))
        for key,target in {'lab':'labs/mirrors/','payload':'assets/demos/mirror-data.json','module':'assets/demos/mirror-compliance.js'}.items():
            template=template.replace('{{'+key+'}}',get_relative_url(target,page.url))
        html=html.replace(marker,template)
    soup=BeautifulSoup(html,'html.parser')
    for paragraph in list(soup.find_all('p')):
        if not paragraph.find('img'):
            continue
        caption=paragraph.find_next_sibling()
        if not caption or caption.name!='p' or not caption.get_text().lstrip().startswith('图 '):
            continue
        figure=soup.new_tag('figure')
        paragraph.insert_before(figure)
        figure.append(paragraph.extract())
        caption.name='figcaption'
        figure.append(caption.extract())
    for quote in soup.find_all('blockquote'):
        quote['class']=['teaching-note']
    return str(soup)
