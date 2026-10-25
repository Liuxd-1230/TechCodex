"""Explicit OCR preprocessing in a separate uv environment; never called by MCP."""
import json
import os
from pathlib import Path
import subprocess
import sys

from .config import ROOT, RagError
from .pdf import text_layer_quality


def ocr_pages(book, start, end, tier='basic', reason=''):
    import pymupdf
    if tier not in ('basic','standard','advanced'):
        raise RagError('OCR tier must be basic, standard or advanced')
    if tier != 'basic' and not reason.strip():
        raise RagError('Higher-quality parsing requires an explicit --reason for the selected pages')
    limit = 20 if tier == 'basic' else 3
    if end-start+1 > limit:
        raise RagError(f'Explicit OCR batches are limited to {limit} pages for tier {tier}')
    pending, skipped = [], []
    pdf_hash = book.pdf_hash()
    cache_root = book.config.cache.parent / 'ocr-mineru' / pdf_hash / tier
    with pymupdf.open(book.config.pdf) as doc:
        if not 1 <= start <= end <= len(doc):
            raise RagError(f'OCR range must be within 1–{len(doc)}')
        for number in range(start,end+1):
            quality = text_layer_quality(doc[number-1])
            existing = cache_root / f'{number}.json'
            if quality['reliable']:
                skipped.append({'pdf_page':number,'reason':'reliable native text layer'})
            elif existing.is_file():
                record = json.loads(existing.read_text(encoding='utf-8'))
                if record.get('schema') != 'techcodex.ocr.v2' or record.get('pdf_sha256') != pdf_hash or record.get('pdf_page') != number:
                    raise RagError('Cached OCR source/page mismatch; preserve and inspect the affected JSON')
                skipped.append({'pdf_page':number,'reason':'cached MinerU result; use a higher tier for selected failures'})
            else:
                pending.append(number)
    if not pending:
        return {'ocr_pages':0,'skipped':skipped}
    default_python = ROOT / '.venv-ocr' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    python = Path(os.environ.get('TECHCODEX_OCR_PYTHON',default_python)).resolve()
    if not python.is_file():
        raise FileNotFoundError('OCR environment missing: create .venv-ocr with uv sync --locked --group ocr')
    home = Path(os.environ.get('TECHCODEX_MINERU_HOME',ROOT/'.local/mineru')).resolve()
    command = [str(python),str(ROOT/'scripts/book_ocr.py'),'parse','--pdf',str(book.config.pdf),
               '--output',str(cache_root),'--pages',','.join(map(str,pending)),
               '--tier',tier,'--home',str(home),'--reason',reason]
    # A fresh process gives OCR no access to the RAG model's device or live CUDA allocations.
    env = {k:v for k,v in os.environ.items() if not k.startswith('MINERU_')}
    env.update(PYTHONIOENCODING='utf-8',CUDA_VISIBLE_DEVICES='-1')
    result = subprocess.run(command,env=env,stdout=subprocess.PIPE,encoding='utf-8')
    if result.returncode:
        raise RagError(f'MinerU {tier} preprocessing failed (exit {result.returncode}); see stderr above')
    return {**json.loads(result.stdout),'skipped':skipped}
