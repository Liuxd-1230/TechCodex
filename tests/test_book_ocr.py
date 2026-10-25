"""OCR contracts with original synthetic pages; no models or copyrighted fixture."""
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pymupdf
import pytest

from rag.config import Config, RagError
from rag.book import Book
from rag.ocr import ocr_pages
from rag.pdf import text_layer_quality


def test_native_text_garbage_and_scan_screening(tmp_path):
    with pymupdf.open() as doc:
        good = doc.new_page()
        good.insert_textbox(pymupdf.Rect(40,40,550,700),'A real text layer about MOS devices and capacitance. '*8)
        assert text_layer_quality(good)['reliable']
        from types import SimpleNamespace
        garbage = SimpleNamespace(get_text=lambda **kwargs:'\ufffd'*200,get_image_info=lambda:[],rect=good.rect)
        assert not text_layer_quality(garbage)['reliable']
        image = good.get_pixmap().tobytes('png')
        scanned = doc.new_page()
        scanned.insert_image(scanned.rect,stream=image)
        assert not text_layer_quality(scanned)['reliable']
        scanned.insert_text((40,40),'Only a partial caption '+'x'*70)
        assert 'short partial text layer' in ' '.join(text_layer_quality(scanned)['reasons'])
        doc.save(tmp_path/'mixed.pdf')
    book = Book(Config(tmp_path/'mixed.pdf',tmp_path/'model',tmp_path/'index',tmp_path/'pages'))
    with patch('rag.ocr.subprocess.run') as run:
        assert ocr_pages(book,1,1)['ocr_pages'] == 0
        run.assert_not_called()
    with pytest.raises(RagError,match='explicit --reason'):
        ocr_pages(book,2,2,tier='standard')
    with pytest.raises(RagError,match='limited to 20'):
        ocr_pages(book,1,21)


def test_mineru_raw_formula_mapping_and_priority(tmp_path):
    with pymupdf.open() as doc:
        doc.new_page()
        doc.set_page_labels([{'startpage':0,'prefix':'','style':'D','firstpagenum':164}])
        doc.save(tmp_path/'book.pdf')
    book = Book(Config(tmp_path/'book.pdf',tmp_path/'model',tmp_path/'index.sqlite3',tmp_path/'pages'))
    formula = r'Z_X=\frac{1}{s C_{eq}}\parallel\frac{C_{GD}+C_{GS}}{g_{m1}C_{GD}}'
    record = {'schema':'techcodex.ocr.v2','pdf_sha256':book.pdf_hash(),'pdf_page':1,
              'provenance':{'engine':'MinerU','version':'4.0.12','tier':'basic','model_fingerprint':'fixture'},
              'text_confidence':None,'review_status':'pending','review_flags':['verify original image'],
              'blocks':[{'type':'equation','text':formula}], 'formulas':[{'latex_raw':formula}]}
    cache = tmp_path/'ocr-mineru'/book.pdf_hash()/'basic'
    cache.mkdir(parents=True)
    (cache/'1.json').write_text(json.dumps(record),encoding='utf-8')
    page = book.read_pages(1)['pages'][0]
    assert page['text'] == formula and page['printed_label'] == '164'
    assert page['ocr']['review_status'] == 'pending'
    assert page['ocr_confidence'] is None
    assert book.page_image(1).read_bytes().startswith(b'\x89PNG')
    assert ocr_pages(book,1,1)['ocr_pages'] == 0
    record['pdf_page'] = 2
    (cache/'1.json').write_text(json.dumps(record),encoding='utf-8')
    with pytest.raises(RagError,match='source-page mapping'):
        book.read_pages(1)


def test_fig614_port_equivalence_from_independent_kcl():
    gm,cgs,cgd = 1e-3,2e-12,.2e-12
    rx = (cgs+cgd)/(gm*cgd)
    ceq = cgs*cgd/(cgs+cgd)
    for frequency in (1e3,1e6,1e8):
        s = 2j*np.pi*frequency
        for rs in (1e-3,1e12):
            # Unit drain test voltage; gate KCL, then drain-current KCL.
            matrix = [[1/rs+s*(cgs+cgd),0],[gm-s*cgd,-1]]
            vx,current = np.linalg.solve(matrix,[s*cgd,-s*cgd])
            if rs < 1:
                assert abs(vx) < 2e-7
                assert np.isclose(current,s*cgd,rtol=2e-6)
            else:
                assert np.isclose(1/current,1/(1/rx+s*ceq),rtol=1e-4)
