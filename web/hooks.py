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
