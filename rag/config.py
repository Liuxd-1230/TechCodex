"""Local configuration; never include book paths or credentials in public sources."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RagError(RuntimeError):
    """An actionable configuration, model or index error."""


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


@dataclass
class Config:
    pdf: Path
    model: Path
    index: Path
    cache: Path
    device: str = 'auto'

    @classmethod
    def load(cls):
        location = Path(os.environ.get('TECHCODEX_RAG_CONFIG', ROOT / '.local/rag.json')).resolve()
        data = json.loads(location.read_text(encoding='utf-8')) if location.is_file() else {}

        def path(key, env, default):
            if os.environ.get(env):
                return Path(os.environ[env]).expanduser().resolve()
            value = Path(data.get(key, default)).expanduser()
            return (location.parent / value).resolve()

        device = os.environ.get('TECHCODEX_RAG_DEVICE', data.get('device', 'auto'))
        if device not in ('auto', 'cpu', 'cuda'):
            raise RagError('device must be auto, cpu or cuda')
        return cls(path('pdf', 'TECHCODEX_BOOK_PDF', 'book.pdf'),
                   path('model', 'TECHCODEX_EMBED_MODEL', 'models/embeddinggemma-2'),
                   path('index', 'TECHCODEX_RAG_INDEX', 'book-rag/book.sqlite3'),
                   path('cache', 'TECHCODEX_RAG_CACHE', 'book-rag/pages'), device)

    def model_missing(self):
        required = ['model.safetensors', 'config.json', 'tokenizer.json',
                    'tokenizer_config.json', 'modules.json', 'config_sentence_transformers.json',
                    'processor_config.json', 'preprocessor_config.json',
                    '1_Pooling/config.json', '2_Normalize/config.json']
        return [name for name in required if not (self.model / name).is_file()]

    def model_identity(self):
        missing = self.model_missing()
        if missing:
            raise FileNotFoundError('Incomplete local EmbeddingGemma 2 directory: ' + ', '.join(missing)
                                    + '; set TECHCODEX_EMBED_MODEL to the complete official snapshot')
        configuration = json.loads((self.model / 'config.json').read_text(encoding='utf-8'))
        if configuration.get('model_type') != 'embedding_gemma2':
            raise RagError('Expected official embedding_gemma2 model configuration')
        files = sorted(p for p in self.model.rglob('*') if p.is_file()
                       and p.suffix in ('.json', '.model', '.jinja', '.safetensors') and p.name != 'source.json')
        fingerprints = {p.relative_to(self.model).as_posix(): sha256(p) for p in files}
        identity = hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode()).hexdigest()
        return {'name': 'google/embeddinggemma-2', 'fingerprint': identity,
                'files': fingerprints, 'dimensions': 768,
                'prefix': 'SearchQuery; documents=title: {section} | text: {paragraph}',
                'source': json.loads((self.model / 'source.json').read_text(encoding='utf-8'))
                if (self.model / 'source.json').is_file() else {'revision': 'local-content-addressed'}}
