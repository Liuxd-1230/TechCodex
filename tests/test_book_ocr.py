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


def test_cloud_import_maps_pages_preserves_math_and_keeps_sources(tmp_path):
    from rag.import_ocr import import_cloud_ocr
    with pymupdf.open() as doc:
        for i in range(3):
            page = doc.new_page()
            page.insert_text((50, 50), f'Original page {i+1}')
            image = page.get_pixmap().tobytes('png')
            page.clean_contents()
            page.insert_image(page.rect, stream=image)
        doc.set_page_labels([{'startpage':0, 'prefix':'', 'style':'D', 'firstpagenum':10}])
        doc.set_toc([[1,'第6章 Frequency response',2]])
        doc.save(tmp_path/'book.pdf')
        with pymupdf.open() as split:
            split.insert_pdf(doc, from_page=1, to_page=2)
            split.save(tmp_path/'split.pdf')
    book = Book(Config(tmp_path/'book.pdf',tmp_path/'model',tmp_path/'index.sqlite3',tmp_path/'pages'))
    formula = r'R_X=\frac{C_{GS}+C_{GD}}{g_{m1}C_{GD}}'
    block = {'type':'text', 'bbox':[0,0,300,50], 'index':0,
             'lines':[{'spans':[{'type':'text','content':'Gate resistance Rs and equivalent Rx: '},
                                {'type':'inline_equation','content':formula,'bbox':[20,20,100,50]}]}]}
    data = {'_version_name':'3.4.4', '_backend':'hybrid', '_effort':'medium',
            'pdf_info':[{'page_idx':i,'page_size':[595,842], 'para_blocks':[block,
                       {'type':'image','blocks':[{'type':'image_caption','lines':[{'spans':[
                           {'type':'text','content':'图6.14 Original circuit'}]}]}]}]} for i in range(2)]}
    export = tmp_path/'cloud.json'
    export.write_text(json.dumps(data), encoding='utf-8')
    report = import_cloud_ocr(book, export, tmp_path/'split.pdf', 2)
    assert report['original_pdf_pages'] == [2,3] and report['formulas'] == 2
    read = book.read_pages(2)['pages'][0]
    assert formula in read['text'] and '图6.14' in read['text']
    assert read['printed_label'] == '11' and read['chapter'] == '6'
    assert read['ocr']['execution'] == 'user-supplied cloud export'
    assert 'ONNX CPU' not in read['extraction'] and read['ocr_confidence'] is None
    record = book.ocr_record(2)
    assert record['split_pdf_page'] == 1 and record['formulas'][0]['latex_raw'] == formula
    assert record['figure_refs'][0]['label'] == '图6.14'
    assert record['provenance']['export_sha256'] and record['review_status'] == 'pending'
    book.index(keyword_only=True)
    assert book.search('Fig. 6.14',mode='keyword')['hits'][0]['pdf_page'] == 2
    assert export.is_file() and book.page_image(2).read_bytes().startswith(b'\x89PNG')
    # Reject incorrect offsets and missing/duplicated export pages before writing any cache.
    with pytest.raises(RagError,match='does not match original'):
        import_cloud_ocr(book, export, tmp_path/'split.pdf', 1)
    data['pdf_info'][1]['page_idx'] = 0
    export.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(RagError,match='sequential'):
        import_cloud_ocr(book, export, tmp_path/'split.pdf', 2)
    assert book.ocr_record(2)['provenance']['export_sha256'] == record['provenance']['export_sha256']
