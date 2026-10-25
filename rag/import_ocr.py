"""Import a private MinerU cloud export against a verified PDF slice; no network/OCR."""
import json
import re
from pathlib import Path

from .book import page_info
from .config import RagError, sha256
from .pdf import text_layer_quality


def block_content(block):
    """Read only paragraph content, not duplicated pre-processing blocks or remote crops."""
    parts, formulas = [], []
    for line in block.get('lines', []):
        spans = []
        for span in line.get('spans', []):
            content = span.get('content', '')
            if 'equation' in span.get('type', ''):
                formulas.append({'latex_raw': content, 'bbox': span.get('bbox'),
                                 'confidence': None, 'needs_review': True})
                display = span['type'] == 'interline_equation'
                content = ('$$' if display else '$') + content + ('$$' if display else '$')
            if content:
                spans.append(content)
        if spans:
            parts.append(' '.join(spans))
    for child in block.get('blocks', []):
        text, child_formulas = block_content(child)
        if text:
            parts.append(text)
        formulas.extend(child_formulas)
    return '\n'.join(parts), formulas


def import_cloud_ocr(book, export, split_pdf, start):
    import pymupdf
    export, split_pdf = Path(export).resolve(), Path(split_pdf).resolve()
    # The source export itself must remain private, not just its converted pages.
    private = book.config.cache.parent.resolve()
    if not export.is_relative_to(private):
        raise RagError('Keep the OCR export inside the private book cache directory before importing')
    data = json.loads(export.read_text(encoding='utf-8-sig'))
    pages = data.get('pdf_info')
    if not isinstance(pages, list) or not pages:
        raise RagError('Expected a MinerU cloud JSON export with a nonempty pdf_info list')
    source_hash = book.pdf_hash()
    provenance = {'engine': 'MinerU', 'version': data.get('_version_name', 'unknown'),
                  'tier': 'cloud', 'execution': 'user-supplied cloud export',
                  'backend': data.get('_backend'), 'effort': data.get('_effort'),
                  'ocr_enabled': data.get('_ocr_enable'), 'vlm': 'not specified by export',
                  'export_file': str(export.relative_to(private)), 'export_sha256': sha256(export),
                  'split_pdf_sha256': sha256(split_pdf), 'original_start_page': start}
    records = []
    with pymupdf.open(book.config.pdf) as original, pymupdf.open(split_pdf) as split:
        if len(pages) != len(split) or not 1 <= start <= start+len(pages)-1 <= len(original):
            raise RagError('Export page count or original PDF range does not match the supplied split PDF')
        for index, page in enumerate(pages):
            if page.get('page_idx') != index:
                raise RagError('Export must contain all split PDF pages in zero-based sequential order')
            number = start + index
            source_page, split_page = original[number-1], split[index]
            if (source_page.rect != split_page.rect or
                source_page.get_pixmap(matrix=pymupdf.Matrix(.25, .25)).digest !=
                    split_page.get_pixmap(matrix=pymupdf.Matrix(.25, .25)).digest):
                raise RagError(f'Split PDF does not match original PDF page {number}')
            size = page.get('page_size', [])
            if len(size) != 2 or min(size) <= 0 or abs(size[0]/size[1] - split_page.rect.width/split_page.rect.height) > .01:
                raise RagError(f'Export page geometry does not match split PDF page {index+1}')
            paragraphs = page.get('para_blocks')
            if not isinstance(paragraphs, list):
                raise RagError(f'Missing paragraph layout on export page {index+1}')
            blocks, formulas = [], []
            for block in paragraphs:
                text, found = block_content(block)
                formulas.extend(found)
                blocks.append({'type': block.get('type', 'text'), 'index': block.get('index'),
                               'bbox': block.get('bbox'), 'text': text, 'raw': block})
            flags = ['Cloud OCR is unreviewed; verify formulas and circuit connections in the original PDF']
            if any(not f['latex_raw'].strip() or f['latex_raw'].count('{') != f['latex_raw'].count('}') for f in formulas):
                flags.append('empty or unbalanced formula transcription')
            if '\ufffd' in ''.join(b['text'] for b in blocks):
                flags.append('replacement characters in OCR text')
            records.append({'schema': 'techcodex.ocr.v2', 'pdf_sha256': source_hash, 'pdf_page': number,
                            **page_info(original, number), 'text_layer': text_layer_quality(source_page),
                            'provenance': provenance, 'blocks': blocks, 'formulas': formulas,
                            'text_confidence': None, 'confidence_kind': 'not provided by cloud export',
                            'review_status': 'pending', 'review_flags': flags,
                            'split_pdf_page': index+1, 'layout_page_size': size,
                            'figure_refs': [{'label': m.group(0), 'block_index': b['index'], 'bbox': b['bbox']}
                                            for b in blocks for m in re.finditer(r'(?:图|Fig\.?|Figure)\s*\d+\.\d+', b['text'], re.I)]})
    output = private/'ocr-mineru'/source_hash/'cloud'
    output.mkdir(parents=True, exist_ok=True)
    for record in records:
        target = output/f'{record["pdf_page"]}.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(target)
    return {'imported_pages': len(records), 'original_pdf_pages': [start, start+len(records)-1],
            'formulas': sum(len(r['formulas']) for r in records), 'provenance': provenance}
