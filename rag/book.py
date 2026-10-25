"""Page-aware extraction, private rendering and incremental hybrid retrieval."""
from collections import defaultdict
from contextlib import contextmanager
import hashlib
import json
import re
import sqlite3
import unicodedata

import numpy as np

from .config import RagError, sha256
from .encoder import Encoder, validate_vectors
from .pdf import text_layer_quality

CHUNK_VERSION = 'paragraph-v3-mineru-layout-raw-math-fts-latex-1400-overlap1'


def normalized(text):
    return unicodedata.normalize('NFKC', text).replace('\x00', '').replace('−', '-')


def terms(text):
    text = normalized(text).lower()
    # Search aliases only: preserve the original LaTeX in stored/readable evidence.
    text = re.sub(r'\\(?:mathrm|textrm|text|mathit|mathbf)\s*\{([^{}]*)\}',r'\1',text)
    text = re.sub(r'\b([rcvgi])\s*_\s*\{([^{}]*)\}',lambda m:m[1]+re.sub(r'\s+','',m[2]),text)
    text = re.sub(r'\b([rcv])[_\s{]+(gs|gd|ds|sb|th|ov|in|out|s|d|o|x)\}?\b',r'\1\2',text)
    figures = re.findall(r'(?:fig(?:ure)?\.?\s*|图\s*)(\d+)\s*[.．-]\s*(\d+)', text)
    words = re.findall(r'[a-z][a-z0-9_]*|\d+\.\d+', text)
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    words += [s[i:i+2] for s in chinese for i in range(max(1, len(s)-1))]
    words += ['fig' + a + 'p' + b for a, b in figures]
    return list(dict.fromkeys(words))


def chunks(blocks, target=1400):
    """Keep PDF paragraphs intact; overlap one short paragraph for equation context."""
    group, length = [], 0
    for block in blocks:
        text = block.strip()
        if not text:
            continue
        if group and length + len(text) > target:
            yield '\n\n'.join(group)
            group = group[-1:] if len(group[-1]) < target // 3 else []
            length = sum(map(len, group))
        group.append(text)
        length += len(text)
    if group:
        yield '\n\n'.join(group)


def ocr_blocks(lines):
    """Keep formula lines with their explanatory sentence, rather than cutting every N lines."""
    group = []
    for line in lines:
        group.append(normalized(line))
        if re.search(r'[。！？]\s*$', line):
            yield '\n'.join(group)
            group = []
    if group:
        yield '\n'.join(group)


def page_info(doc, number):
    chapter, section = '', ''
    for level, title, page in doc.get_toc():
        if page > number:
            continue
        title = normalized(title).strip()
        match = re.match(r'(?:第\s*(\d+)\s*章|chapter\s+(\d+))', title, re.I)
        if match:
            chapter = next(x for x in match.groups() if x)
            section = title
        elif level >= 2:
            section = title
    label = doc[number-1].get_label() if doc.get_page_labels() else None
    return {'chapter': chapter, 'section': section, 'printed_label': label,
            'label_source': 'PDF page label' if label else 'unavailable; cite PDF page'}


class Book:
    def __init__(self, config):
        self.config = config
        self.encoder = Encoder(config)
        self.visual_encoder = None
        self._identity = None
        self._pdf_stamp = None
        self._pdf_hash = None

    def pdf_hash(self):
        if not self.config.pdf.is_file():
            raise FileNotFoundError('Textbook PDF missing; set TECHCODEX_BOOK_PDF or .local/rag.json')
        stat = self.config.pdf.stat()
        stamp = (stat.st_size, stat.st_mtime_ns)
        if stamp != self._pdf_stamp:
            self._pdf_hash, self._pdf_stamp = sha256(self.config.pdf), stamp
        return self._pdf_hash

    @contextmanager
    def connect(self, create=False):
        if not create and not self.config.index.is_file():
            raise RagError('No book index. Run: python -m rag index (explicit local indexing required)')
        self.config.index.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.config.index)
        try:
            db.row_factory = sqlite3.Row
            if create:
                db.executescript('''
                CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS pages(page INTEGER PRIMARY KEY,digest TEXT,info TEXT,quality TEXT,state TEXT);
                CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY,page INTEGER,title TEXT,text TEXT,
                    figures TEXT,equations TEXT,vector BLOB,model TEXT);
                CREATE INDEX IF NOT EXISTS chunks_page ON chunks(page);
                CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(id UNINDEXED, words);
                CREATE TABLE IF NOT EXISTS visuals(page INTEGER PRIMARY KEY,vector BLOB,model TEXT,pdf TEXT);
                ''')
            elif db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RagError('SQLite index is corrupt; restore or explicitly rebuild the private index')
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def metadata(db):
        return {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM meta')}

    @staticmethod
    def put_meta(db, key, value):
        db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (key, json.dumps(value, ensure_ascii=False)))

    def identity(self):
        if self._identity is None:
            self._identity = self.config.model_identity()
        return self._identity

    def ocr_record(self, number):
        base = self.config.cache.parent
        for tier in ('cloud','advanced','standard','basic'):
            path = base/'ocr-mineru'/self.pdf_hash()/tier/f'{number}.json'
            if path.is_file():
                record = json.loads(path.read_text(encoding='utf-8'))
                if record.get('schema') != 'techcodex.ocr.v2' or record.get('pdf_sha256') != self.pdf_hash() or record.get('pdf_page') != number:
                    raise RagError('MinerU OCR cache schema or source-page mapping mismatch')
                return record
        legacy = base/'ocr'/self.pdf_hash()/f'{number}.json'
        if legacy.is_file():
            record = json.loads(legacy.read_text(encoding='utf-8'))
            if record['pdf_sha256'] != self.pdf_hash() or record['pdf_page'] != number:
                raise RagError('Legacy OCR cache source mismatch')
            return record
        return None

    def ocr_metadata(self, number):
        record = self.ocr_record(number)
        if not record:
            return {}
        provenance = record.get('provenance',{})
        return {'engine':provenance.get('engine'),'version':provenance.get('version'),
                'tier':provenance.get('tier'),'model_fingerprint':provenance.get('model_fingerprint'),
                'vlm':provenance.get('vlm'),
                'execution':provenance.get('execution', 'local ONNX CPU' if record.get('schema') == 'techcodex.ocr.v2' else 'legacy RapidOCR'),
                'export_file':provenance.get('export_file'),'export_sha256':provenance.get('export_sha256'),
                'review_status':record.get('review_status','unreviewed legacy OCR'),
                'review_flags':record.get('review_flags',['OCR symbols need original-image verification']),
                'formula_count':len(record.get('formulas',[]))}

    def page_blocks(self, page, number):
        blocks = [b[4].replace('\x00','') for b in page.get_text('blocks', sort=True) if b[6] == 0]
        source, confidence = 'PDF text', None
        if not text_layer_quality(page)['reliable']:
            record = self.ocr_record(number)
            if record and record.get('schema') == 'techcodex.ocr.v2':
                blocks = [b['text'] for b in record['blocks'] if b['text'].strip() and
                          b['type'] not in ('header','footer','page_number')]
                provenance = record['provenance']
                execution = provenance.get('execution', 'local ONNX CPU')
                source = f'MinerU {provenance["version"]} {provenance["tier"]} {execution}; original math transcription'
                confidence = record['text_confidence']
            elif record:
                blocks = list(ocr_blocks(record['lines']))
                source, confidence = 'legacy RapidOCR; verify symbols in original image', record['mean_confidence']
        return blocks, source, confidence

    def index(self, keyword_only=False):
        import pymupdf
        pdf_hash = self.pdf_hash()
        identity = None if keyword_only else self.identity()
        with self.connect(create=True) as db, pymupdf.open(self.config.pdf) as doc:
            old = self.metadata(db)
            if old.get('chunk_version') not in (None, CHUNK_VERSION):
                db.execute('DELETE FROM pages')
            if identity and old.get('model', {}).get('fingerprint') != identity['fingerprint']:
                db.execute('UPDATE chunks SET vector=NULL, model=NULL')
                db.execute('DELETE FROM visuals')
            counts = defaultdict(int)
            for number in range(1, len(doc)+1):
                page = doc[number-1]
                blocks, source, confidence = self.page_blocks(page, number)
                text = '\n'.join(blocks)
                info = page_info(doc, number)
                info.update(extraction=source, ocr_confidence=confidence)
                if not text_layer_quality(page)['reliable']:
                    info['ocr'] = self.ocr_metadata(number)
                digest = hashlib.sha256((text + json.dumps(info, ensure_ascii=False)).encode()).hexdigest()
                previous = db.execute('SELECT digest FROM pages WHERE page=?', (number,)).fetchone()
                if previous and previous[0] == digest:
                    counts['pages_skipped'] += 1
                    continue
                quality = 'poor extraction: inspect original page' if (len(text.strip()) < 40 or
                    (confidence is not None and confidence < .70) or
                    sum(c == '\ufffd' or 0xE000 <= ord(c) <= 0xF8FF for c in text) / max(1, len(text)) > .02) else 'ok'
                previous_chunks = {r['id']: r for r in db.execute('SELECT id,vector,model FROM chunks WHERE page=?', (number,))}
                for key in previous_chunks:
                    db.execute('DELETE FROM fts WHERE id=?', (key,))
                db.execute('DELETE FROM chunks WHERE page=?', (number,))
                if quality == 'ok':
                    for i, chunk in enumerate(chunks(blocks)):
                        key = hashlib.sha256(f'{number}:{i}:{info["section"]}:{chunk}'.encode()).hexdigest()
                        figures = re.findall(r'(?:图|Fig\.?|Figure)\s*\d+\s*[.．-]\s*\d+', chunk, re.I)
                        equations = re.findall(r'[（(]\s*\d+\s*[.．-]\s*\d+\s*[）)]', chunk)
                        equations += re.findall(r'\\tag\{\d+\.\d+\}',chunk)
                        previous_chunk = previous_chunks.get(key)
                        vector, model = (previous_chunk['vector'],previous_chunk['model']) if previous_chunk else (None,None)
                        db.execute('INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)',
                                   (key, number, info['section'], chunk, json.dumps(figures), json.dumps(equations),vector,model))
                        if vector is not None:
                            counts['chunks_reused'] += 1
                        db.execute('INSERT INTO fts VALUES (?,?)', (key, ' '.join(terms(chunk + ' ' + info['section']))))
                db.execute('INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?)',
                           (number, digest, json.dumps(info, ensure_ascii=False), quality, 'text_ready'))
                db.execute('DELETE FROM visuals WHERE page=?', (number,))
                counts['pages_extracted'] += 1
                counts['poor_pages'] += quality != 'ok'
            for row in db.execute('SELECT id FROM chunks WHERE page>?', (len(doc),)).fetchall():
                db.execute('DELETE FROM fts WHERE id=?', (row[0],))
            db.execute('DELETE FROM chunks WHERE page>?', (len(doc),))
            db.execute('DELETE FROM pages WHERE page>?', (len(doc),))
            db.execute('DELETE FROM visuals WHERE page>?', (len(doc),))
            for key, value in [('pdf_sha256', pdf_hash), ('page_count', len(doc)),
                               ('chunk_version', CHUNK_VERSION), ('dimensions', 768)]:
                self.put_meta(db, key, value)
            if identity:
                self.put_meta(db, 'model', identity)
            db.commit()  # Text remains usable if a later embedding batch fails.
            if identity:
                pending = db.execute('SELECT * FROM chunks WHERE vector IS NULL ORDER BY page,id').fetchall()
                for start in range(0, len(pending), 8):
                    batch = pending[start:start+8]
                    vectors = self.encoder.encode(['title: ' + r['title'] + ' | text: ' + r['text'] for r in batch])
                    for row, vector in zip(batch, vectors):
                        db.execute('UPDATE chunks SET vector=?,model=? WHERE id=?',
                                   (vector.tobytes(), identity['fingerprint'], row['id']))
                    db.commit()
                    counts['chunks_encoded'] += len(batch)
                    if start % 160 == 0:
                        import logging
                        logging.getLogger(__name__).info('Encoded %d/%d pending chunks', start+len(batch), len(pending))
                db.execute("UPDATE pages SET state='complete' WHERE quality='ok' AND NOT EXISTS "
                           '(SELECT 1 FROM chunks WHERE chunks.page=pages.page AND vector IS NULL)')
            return dict(counts)

    def _assert_source(self, db):
        if self.metadata(db).get('pdf_sha256') != self.pdf_hash():
            raise RagError('PDF changed since indexing; run python -m rag index before using old citations')

    def search(self, query, chapter=None, top_k=5, mode='hybrid'):
        if not query.strip() or len(query) > 2000 or not 1 <= top_k <= 10:
            raise RagError('Use a nonempty query <=2000 characters and top_k between 1 and 10')
        if mode not in ('hybrid', 'keyword', 'semantic', 'visual'):
            raise RagError('mode must be hybrid, keyword, semantic or visual')
        warnings, ranks, similarities = [], [], {}
        semantic_used = False
        with self.connect() as db:
            self._assert_source(db)
            meta = self.metadata(db)
            if meta.get('dimensions') != 768:
                raise RagError('Index dimensions do not match the 768-dimensional encoder; explicitly rebuild')
            coverage = dict(db.execute('SELECT count(*) AS pages, sum(quality=\'ok\') AS readable_pages FROM pages').fetchone())
            if coverage['readable_pages'] != coverage['pages']:
                warnings.append(f'Partial text coverage: {coverage["readable_pages"]}/{coverage["pages"]} pages; '
                                'poor/scanned pages need explicit OCR and reindexing')
            rows = {r['id']: dict(r) for r in db.execute('SELECT c.*,p.info FROM chunks c JOIN pages p ON c.page=p.page')
                    if chapter is None or json.loads(r['info'])['chapter'] == str(chapter)}
            if mode in ('keyword', 'hybrid'):
                tokens = terms(query)[:64]
                figures = [t for t in tokens if re.fullmatch(r'fig\d+p\d+',t)]
                symbols = [t for t in tokens if re.fullmatch(
                    r'(?:r(?:s|x|d|o|in|out)|c(?:gd|gs|db|sb|l|i|o|f)|'
                    r'v(?:gs|ds|sb|in|out|th|ov)|g(?:m|ds|mb))\d*',t)]

                def keyword_rank(expression):
                    candidates = db.execute('SELECT fts.id,bm25(fts) AS rank FROM fts '
                                            'JOIN chunks c ON c.id=fts.id JOIN pages p ON c.page=p.page '
                                            'WHERE fts MATCH ? AND (? IS NULL OR json_extract(p.info,\'$.chapter\')=?) '
                                            'ORDER BY rank LIMIT 150',
                                            (expression, None if chapter is None else str(chapter), str(chapter))).fetchall() if expression else []
                    return [r['id'] for r in candidates if r['id'] in rows]

                expression = ' OR '.join('"'+t+'"' for t in (figures or tokens))
                exact_symbols = mode == 'keyword' and symbols and set(tokens) == set(symbols)
                if exact_symbols:
                    expression = ' AND '.join('"'+t+'"' for t in symbols)
                ranks.append(keyword_rank(expression))
                if len(symbols) >= 2 and not figures and not exact_symbols:
                    from itertools import combinations
                    pairs = ['("'+a+'" AND "'+b+'")' for a,b in combinations(symbols[:6],2)]
                    ranks.append(keyword_rank(' OR '.join(pairs)))
            if mode != 'keyword':
                try:
                    identity = self.identity()
                except FileNotFoundError as exc:
                    if mode != 'hybrid':
                        raise
                    warnings.append(f'Keyword fallback: {exc}')
                    identity = None
                if identity:
                    if not meta.get('model'):
                        if mode != 'hybrid':
                            raise RagError('Text index has no model vectors yet; run python -m rag index')
                        warnings.append('Keyword fallback: text-only index; run python -m rag index for vectors')
                        identity = None
                    elif meta['model'].get('fingerprint') != identity['fingerprint']:
                        raise RagError('Model/tokenizer changed; explicitly reindex before vector retrieval')
                if identity:
                    try:
                        query_vector = self.encoder.encode([query], query=True)[0]
                    except ImportError as exc:
                        if mode != 'hybrid':
                            raise
                        warnings.append(f'Keyword fallback; embedding dependency unavailable: {exc}')
                        query_vector = None
                else:
                    query_vector = None
                if query_vector is not None:
                    if mode == 'visual':
                        visual = db.execute('SELECT * FROM visuals').fetchall()
                        ranked = []
                        for r in visual:
                            if r['pdf'] != meta['pdf_sha256']:
                                continue
                            info = db.execute('SELECT info FROM pages WHERE page=?',(r['page'],)).fetchone()
                            if chapter is not None and json.loads(info[0])['chapter'] != str(chapter):
                                continue
                            vector = validate_vectors(np.frombuffer(r['vector'], dtype=np.float32)[None, :], 1)[0]
                            score = float(query_vector @ vector)
                            ranked.append({'pdf_page': r['page'], 'cosine': score})
                        ranked.sort(key=lambda r: r['cosine'], reverse=True)
                        return {'mode': 'visual', 'source_sha256': meta['pdf_sha256'], 'hits': ranked[:top_k],
                                'warning': 'Selected-page visual index only; verify circuitry in original page image'}
                    keys = [key for key, r in rows.items() if r['vector'] is not None]
                    if keys:
                        vectors = validate_vectors(np.stack([np.frombuffer(rows[k]['vector'], dtype=np.float32) for k in keys]), len(keys))
                        scores = vectors @ query_vector
                        order = np.argsort(-scores)[:100]
                        ranks.append([keys[i] for i in order])
                        similarities = {keys[i]: float(scores[i]) for i in order}
                        semantic_used = True
                        if len(keys) < len(rows):
                            warnings.append(f'Partial vector coverage: {len(keys)}/{len(rows)} candidate chunks')
                    else:
                        warnings.append('No text vectors yet; run python -m rag index')
            fused, representatives = defaultdict(float), {}
            for ranking in ranks:
                seen = set()
                for key in ranking:
                    page = rows[key]['page']
                    if page in seen:
                        continue
                    seen.add(page)
                    fused[page] += 1 / (60 + len(seen))
                    representatives.setdefault(page,key)
            hits = []
            for page in sorted(fused, key=fused.get, reverse=True):
                r = rows[representatives[page]]
                info = json.loads(r['info'])
                hits.append({'pdf_page': r['page'], 'page_range': [r['page'], r['page']], **info,
                             'snippet': r['text'][:500], 'figures': json.loads(r['figures']),
                             'equations': json.loads(r['equations']), 'rrf_score': fused[page],
                             'cosine': max((similarities[k] for k in similarities if rows[k]['page']==page),default=None),
                             'source_sha256': meta['pdf_sha256'],
                             'neighbor_pages': list(range(max(1,r['page']-1), min(meta['page_count'],r['page']+1)+1))})
                if len(hits) == top_k:
                    break
            return {'mode': 'keyword' if mode == 'hybrid' and not semantic_used else mode,
                    'coverage': coverage, 'warnings': warnings, 'hits': hits}

    def read_pages(self, start, count=1):
        import pymupdf
        if not 1 <= count <= 3:
            raise RagError('Read 1–3 consecutive PDF pages per call')
        source = self.pdf_hash()
        with pymupdf.open(self.config.pdf) as doc:
            if start < 1 or start + count - 1 > len(doc):
                raise RagError(f'PDF page range must be within 1–{len(doc)}')
            pages = []
            for p in range(start,start+count):
                blocks, extraction, confidence = self.page_blocks(doc[p-1],p)
                pages.append({'pdf_page': p, **page_info(doc,p), 'extraction': extraction,
                              'ocr_confidence': confidence, 'ocr':self.ocr_metadata(p) if extraction!='PDF text' else {},
                              'text': '\n\n'.join(blocks)[:12000]})
            return {'source_sha256': source, 'pages': pages}

    def page_image(self, number):
        import pymupdf
        source = self.pdf_hash()
        with pymupdf.open(self.config.pdf) as doc:
            if not 1 <= number <= len(doc):
                raise RagError(f'PDF page must be within 1–{len(doc)}')
            target = self.config.cache / source[:16] / f'page-{number}.png'
            if not target.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                page = doc[number-1]
                scale = min(1600 / page.rect.width, 2000 / page.rect.height)
                page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).save(target)
            return target

    def index_images(self, pages):
        if not pages or len(pages) > 20:
            raise RagError('Select 1–20 individual pages; never implicitly render the whole book')
        try:
            if self.visual_encoder is None:
                self.visual_encoder = Encoder(self.config, vision=True)
            identity = self.identity()
            with self.connect() as db:
                self._assert_source(db)
                meta = self.metadata(db)
                if meta.get('model', {}).get('fingerprint', identity['fingerprint']) != identity['fingerprint']:
                    raise RagError('Model changed; reindex the text index before adding visual vectors')
                self.put_meta(db,'model',identity)
                for page in pages:
                    image = self.page_image(page)
                    vector = self.visual_encoder.encode([{'image': str(image)}])[0]
                    db.execute('INSERT OR REPLACE INTO visuals VALUES (?,?,?,?)',
                               (page, vector.tobytes(), identity['fingerprint'], self.pdf_hash()))
            return {'pages_encoded': pages, 'device': self.visual_encoder.status()}
        except (ImportError, NotImplementedError) as exc:
            return {'vision_available': False, 'reason': str(exc), 'text_and_page_images': 'unaffected'}

    def status(self):
        result = {'pdf_available': self.config.pdf.is_file(), 'model_missing': self.config.model_missing(),
                  'index_available': self.config.index.is_file(), 'text_device': self.encoder.status(),
                  'configured_device': self.config.device,
                  'visual_device': self.visual_encoder.status() if self.visual_encoder else {'loaded': False}}
        if self.config.index.is_file():
            with self.connect() as db:
                result['metadata'] = {k: v for k, v in self.metadata(db).items() if k != 'model'}
                recorded_model = self.metadata(db).get('model',{})
                result['indexed_model'] = {k:v for k,v in recorded_model.items() if k != 'files'}
                result['pages'] = db.execute('SELECT count(*) FROM pages').fetchone()[0]
                result['poor_pages'] = db.execute("SELECT count(*) FROM pages WHERE quality!='ok'").fetchone()[0]
                result['chunks'] = db.execute('SELECT count(*) FROM chunks').fetchone()[0]
                result['vectors'] = db.execute('SELECT count(*) FROM chunks WHERE vector IS NOT NULL').fetchone()[0]
                result['visual_pages'] = db.execute('SELECT count(*) FROM visuals').fetchone()[0]
                result['ocr_sources'] = [dict(r) for r in db.execute(
                    "SELECT json_extract(info,'$.ocr.engine') AS engine, json_extract(info,'$.ocr.tier') AS tier, "
                    "count(*) AS pages FROM pages GROUP BY engine,tier")]
        return result
