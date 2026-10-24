"""Turn native Markdown image/caption pairs into semantic textbook figures."""
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
import sys
from urllib.parse import quote
from mkdocs.utils import get_relative_url

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from book import ROUTES, repository_url


def on_page_markdown(markdown,page,config,files):
    chapters={'devices':('2','MOS 器件'),'stages':('3','单级放大器'),'differential':('4','差分放大器'),'mirrors':('5','电流镜与偏置'),'frequency':('6','频率响应'),'noise':('7','噪声')}
    parts=page.url.split('/')
    if len(parts)>1 and parts[0]=='analog' and parts[1] in chapters:
        number,subject=chapters[parts[1]]
        page.meta.update(book_chapter=number,book_subject=subject,book_index='analog/'+parts[1]+'/')
    original=next((src for src,dest in ROUTES.items() if dest==page.file.src_uri),page.file.src_uri)
    page.edit_url='https://github.com/Liuxd-1230/TechCodex/blob/main/'+quote(original,safe='/')
    # GitHub understands Markdown inside native details. Python-Markdown needs
    # an explicit opt-in, added only while rendering the site.
    return markdown.replace('<details>','<details markdown="1">')


def on_page_content(html,page,config,files):
    for slug in ('mos-channel','differential-modes','ota-frequency'):
        marker=f'<!-- interactive: {slug} -->'
        if marker not in html:
            continue
        template=(Path(__file__).parent/'demos'/f'{slug}.html').read_text(encoding='utf-8')
        for key,target in {'module':f'assets/demos/{slug}.js','payload':'assets/demos/ota-frequency-data.json','lab':'labs/frequency/'}.items():
            template=template.replace('{{'+key+'}}',get_relative_url(target,page.url))
        if slug=='differential-modes':
            drawing=BeautifulSoup((Path(__file__).resolve().parents[1]/'模拟/图/diff-modes.svg').read_text(encoding='utf-8'),'html.parser')
            for style in drawing.select('style'):
                style.decompose()
            template=template.replace('{{schematic}}',str(drawing.svg))
        html=html.replace(marker,template)
    marker='<!-- interactive: source-follower -->'
    if marker in html:
        template=(Path(__file__).parent/'demos/source-follower.html').read_text(encoding='utf-8')
        template=template.replace('{{module}}',get_relative_url('assets/demos/source-follower.js',page.url))
        html=html.replace(marker,template)
    marker='<!-- interactive: noise-band -->'
    if marker in html:
        template=(Path(__file__).parent/'demos/noise-band.html').read_text(encoding='utf-8')
        for key,target in {'lab':'labs/noise/','payload':'assets/demos/noise-data.json','module':'assets/demos/noise-band.js'}.items():
            template=template.replace('{{'+key+'}}',get_relative_url(target,page.url))
        html=html.replace(marker,template)
    marker='<!-- interactive: miller-poles -->'
    if marker in html:
        template=(Path(__file__).parent/'demos/miller-poles.html').read_text(encoding='utf-8')
        template=template.replace('{{schematic}}',(Path(__file__).parent/'demos/miller-schematic.svg').read_text(encoding='utf-8'))
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
            'payload':'assets/demos/steering-data.json',
            'module':'assets/demos/current-steering.js',
        }
        for key,target in targets.items():
            template=template.replace('{{'+key+'}}',get_relative_url(target,page.url))
        template=template.replace('{{csv}}',repository_url('模拟/实验/差分对/data/ideal-steering-sweep.csv'))
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
        image=figure.find('img')
        stem=Path(image.get('src','')).stem
        if stem in ('mos-channel','diff-modes','cs-load-resistor','cs-load-diode','cs-load-current','ota-current-sum','noise-statistics',
                    'mos-charge-increment','cg-termination','cascode-feedback'):
            figure['id']='figure-'+stem
        if stem in ('mos-charge','sf-feedback','noise-referral','noise-paths'):
            figure['class']=['concept-figure']
            figure['id']='figure-'+Path(image['src']).stem
            paragraph.name='div'
            paragraph['class']=['diagram-viewport']
            paragraph['role']='region'
            paragraph['tabindex']='0'
            paragraph['aria-label']=image.get('alt','概念图')+'，窄屏可横向查看'
            hint=soup.new_tag('p',attrs={'class':'diagram-scroll-hint'})
            hint.string='图内可左右查看，或使用下方的“查看原图”。'
            paragraph.insert_before(hint)
        if not image.find_parent('a'):
            link=soup.new_tag('a',href=image['src'],title='打开原图，查看细节')
            link['aria-label']=image.get('alt','技术图')+' · 打开原图'
            image.wrap(link)
        # A visible, native link makes detail viewing discoverable on phones.
        # Keep the ordinary Markdown image/caption untouched in the repository.
        detail=soup.new_tag('a',href=image['src'])
        detail['class']=['figure-detail']
        detail['aria-label']=image.get('alt','技术图')+' · 查看原图'
        detail.string='查看原图'
        caption.append(' ')
        caption.append(detail)
    direct=soup.find('img',src=lambda value:value and 'sf-load-direct.svg' in value)
    if direct:
        before=direct.find_parent('figure')
        after=before.find_next_sibling('figure') if before else None
        if after and after.find('img',src=lambda value:value and 'sf-load-buffer.svg' in value):
            pair=soup.new_tag('div',attrs={'class':'sf-loading-pair'})
            before.insert_before(pair);pair.append(before.extract());pair.append(after.extract())
    load_figures=[soup.find(id='figure-cs-load-'+name) for name in ('resistor','diode','current')]
    if all(load_figures):
        comparison=soup.new_tag('div',attrs={'class':'load-comparison'})
        load_figures[0].insert_before(comparison)
        for figure in load_figures:
            comparison.append(figure.extract())
    for quote in soup.find_all('blockquote'):
        quote['class']=['teaching-note']
    if page.url=='':
        home=(Path(__file__).parent/'home.html').read_text(encoding='utf-8')
        for key,target in {'devices':'analog/devices/','chapters':'analog/','stages':'analog/stages/','differential':'analog/differential/','mirrors':'analog/mirrors/','frequency':'analog/frequency/','noise':'analog/noise/'}.items():
            home=home.replace('{{'+key+'}}',get_relative_url(target,page.url))
        heading=soup.find('h1')
        if heading:heading.replace_with(BeautifulSoup(home,'html.parser'))
        subtitle=soup.find('h2')
        if subtitle and subtitle.get_text().startswith('从零开始的模电生活'):subtitle.decompose()
        table=soup.find('table')
        if table:
            disclosure=soup.new_tag('details');summary=soup.new_tag('summary');summary.string='按具体问题查阅'
            table.insert_before(disclosure);disclosure.append(summary);disclosure.append(table.extract())
    return str(soup)


def on_post_page(output,page,config):
    # Stable source filenames remain readable in GitHub. Content hashes prevent
    # a newly deployed reading system being paired with a cached previous CSS.
    for name in ('book.css','book.js','demos/circuit-demo.css',
                 'demos/current-steering.js','demos/mirror-compliance.js',
                 'demos/miller-poles.js','demos/noise-band.js',
                 'demos/source-follower.css','demos/source-follower.js',
                 'demos/teaching-examples.css','demos/mos-channel.js',
                 'demos/differential-modes.js','demos/ota-frequency.css','demos/ota-frequency.js'):
        path=Path(__file__).parent/'assets'/name
        url=get_relative_url('assets/'+name,page.url)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        for attr in ('href','src'):
            output=output.replace(f'{attr}="{url}"',f'{attr}="{url}?v={digest}"')
    return output
