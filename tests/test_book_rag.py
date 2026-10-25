"""Small synthetic fixtures: no copyrighted text, downloads or real model required."""
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
import pymupdf

from rag.book import Book, chunks, terms
from rag.config import Config, RagError
from rag.encoder import Encoder, validate_vectors


@pytest.fixture
def book(tmp_path):
    pdf = tmp_path / 'book.pdf'
    with pymupdf.open() as doc:
        for text in ['Chapter 6 Frequency response. Fig. 6.14 Cgd Rs Rx. ' * 8,
                     'Gate node X and drain feedback, neighboring context. ' * 8]:
            page = doc.new_page()
            page.insert_textbox(pymupdf.Rect(40,40,550,700), text)
        doc.set_toc([[1,'Chapter 6 Frequency response',1],[2,'6.2 Miller effect',1]])
        doc.save(pdf)
    return Book(Config(pdf, tmp_path/'missing', tmp_path/'index.sqlite3', tmp_path/'images'))


def test_incremental_and_symbols(book):
    first = book.index(keyword_only=True)
    second = book.index(keyword_only=True)
    assert first['pages_extracted'] == 2 and second == {'pages_skipped': 2}
    for query in ['Fig. 6.14', 'Cgd Rs Rx']:
        hit = book.search(query, chapter='6', mode='keyword')['hits'][0]
        assert hit['pdf_page'] == 1 and hit['neighbor_pages'] == [1,2]
        assert hit['source_sha256'] == book.pdf_hash()
    fallback = book.search('Cgd', mode='hybrid')
    assert fallback['mode'] == 'keyword' and 'Incomplete' in fallback['warnings'][0]
    assert book.encoder.model is None
    with patch.object(book,'identity',return_value={'fingerprint':'ready'}):
        assert book.search('Cgd')['mode'] == 'keyword'


def test_chinese_normalization():
    assert {'源跟','跟随','fig6p14','vgs','cgd'} <= set(terms('源跟随 Fig. 6.14 VGS Cgd'))
    assert 'vgs' in terms('ＶＧＳ')
    assert {'cgd','vgs','rs'} <= set(terms('C_{gd} V_GS Rₛ'))
    assert {'cgd','rs','gm1'} <= set(terms(r'C_{\mathrm{GD}} R_{\mathrm{S}} g_{m1}'))
    paragraph = 'a'*800
    assert list(chunks([paragraph, paragraph])) == [paragraph, paragraph]


def test_original_image_and_bounded_read(book):
    assert book.page_image(1).read_bytes().startswith(b'\x89PNG')
    assert book.read_pages(1,2)['pages'][1]['pdf_page'] == 2
    with pytest.raises(RagError):
        book.read_pages(1,4)
    with pytest.raises(RagError):
        book.page_image(0)


def test_changed_source_and_vector_corruption(book):
    book.index(keyword_only=True)
    book.config.pdf.write_bytes(book.config.pdf.read_bytes() + b'\n')
    with pytest.raises(RagError, match='PDF changed'):
        book.search('Cgd', mode='keyword')
    for values in [np.zeros((1,768)), np.ones((1,767)), np.full((1,768), np.nan)]:
        with pytest.raises(RagError):
            validate_vectors(values, 1)


def test_missing_index_is_not_implicit_index(book):
    with pytest.raises(RagError, match='explicit local indexing'):
        book.search('gate')
    assert not book.config.index.exists()


def test_connection_closed_after_tool_operation(book):
    import sqlite3
    with book.connect(create=True) as db:
        assert db.execute('SELECT 1').fetchone()[0] == 1
    with pytest.raises(sqlite3.ProgrammingError,match='closed'):
        db.execute('SELECT 1')


def test_device_unavailable_and_bounded_oom(book):
    import torch
    vector = np.zeros((2,768), np.float32)
    vector[:,0] = 1
    encoder = Encoder(book.config)
    loads = []
    attempts = []

    class FakeModel:
        def encode(self, texts, **kwargs):
            attempts.append((encoder.device,kwargs['batch_size']))
            if encoder.device == 'cuda':
                raise torch.cuda.OutOfMemoryError('injected test OOM')
            return vector

    def load(device):
        loads.append(device)
        encoder.device, encoder.dtype, encoder.model = device, 'float32', FakeModel()

    with patch.object(encoder, '_load', side_effect=load), patch('torch.cuda.is_available', return_value=False):
        assert encoder.encode(['a','b']).shape == (2,768)
        assert loads == ['cpu'] and encoder.fallback == 'CUDA unavailable'
    encoder.model = None
    loads.clear()
    attempts.clear()
    with patch.object(encoder, '_load', side_effect=load), patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.init'), patch('torch.cuda.empty_cache'):
        assert encoder.encode(['a','b']).shape == (2,768)
        assert loads == ['cuda','cpu'] and 'OOM' in encoder.fallback
        assert attempts == [('cuda',4),('cuda',2),('cpu',2)]
    book.config.device = 'cuda'
    encoder = Encoder(book.config)
    with patch('torch.cuda.is_available', return_value=False), pytest.raises(RagError, match='Explicit CUDA'):
        encoder.encode(['a'])


def test_config_failure_not_gpu_fallback(book):
    import torch
    encoder = Encoder(book.config)
    with patch('torch.cuda.is_available', return_value=True), patch('torch.cuda.init'), \
         patch.object(encoder, '_load', side_effect=ValueError('broken config')), \
         pytest.raises(ValueError, match='broken config'):
        encoder.encode(['a'])
    assert encoder.fallback is None


def test_model_identity_and_incremental_vectors(book):
    with pytest.raises(FileNotFoundError, match='tokenizer'):
        book.config.model_identity()
    identity = {'fingerprint':'test-model', 'dimensions':768}
    encoded = []

    def encode(texts, **kwargs):
        encoded.extend(texts)
        vectors = np.zeros((len(texts),768),np.float32)
        vectors[:,0] = 1
        return vectors

    with patch.object(book,'identity',return_value=identity), patch.object(book.encoder,'encode',side_effect=encode):
        first = book.index()
        assert first['chunks_encoded'] == len(encoded) > 0
        encoded.clear()
        book.config.device = 'cpu'
        assert book.index() == {'pages_skipped':2} and encoded == []
        assert book.search('Fig. 6.14',chapter='6')['hits'][0]['pdf_page'] == 1
    with patch.object(book,'identity',return_value={'fingerprint':'changed'}), \
         pytest.raises(RagError,match='Model/tokenizer changed'):
        book.search('gate')


def test_publish_guard():
    from scripts.book import assert_public_asset
    for name in ['book.pdf','model.safetensors','model.onnx','model.gguf','model_output.json','tokenizer.json','vectors.npy','index.sqlite3']:
        with pytest.raises(RuntimeError):
            assert_public_asset(Path('web/assets')/name)
    assert_public_asset(Path('web/assets/demos/data.json'))
