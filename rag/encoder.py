"""Offline EmbeddingGemma 2, with bounded CUDA recovery and validated vectors."""
import gc
import logging
import os
import numpy as np

from .config import RagError

log = logging.getLogger(__name__)


def validate_vectors(values, count):
    values = np.asarray(values, dtype=np.float32)
    if values.shape != (count, 768) or not np.isfinite(values).all():
        raise RagError(f'Invalid embedding shape or non-finite values: {values.shape}; expected ({count}, 768)')
    norms = np.linalg.norm(values, axis=1)
    if not np.allclose(norms, 1, atol=2e-3):
        raise RagError('Embedding vectors must be normalized, finite and nonzero')
    return values


class Encoder:
    def __init__(self, config, vision=False):
        self.config, self.vision = config, vision
        self.model = None
        self.device = self.dtype = None
        self.fallback = None

    def _load(self, device):
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        import torch
        from sentence_transformers import SentenceTransformer
        missing = self.config.model_missing()
        if missing:
            raise FileNotFoundError('Incomplete local model: ' + ', '.join(missing))
        dtype = torch.bfloat16 if device == 'cuda' and torch.cuda.is_bf16_supported() else torch.float32
        config_kwargs = {'audio_config': None}
        if not self.vision:
            config_kwargs['vision_config'] = None
        # No remote code, model IDs or network resolution is allowed here.
        self.model = SentenceTransformer(str(self.config.model), device=device,
                                        local_files_only=True, trust_remote_code=False,
                                        config_kwargs=config_kwargs, model_kwargs={'dtype': dtype})
        self.device, self.dtype = device, str(dtype).removeprefix('torch.')
        log.info('EmbeddingGemma 2 loaded: device=%s dtype=%s vision=%s', device, self.dtype, self.vision)

    def _cpu(self, reason):
        import torch
        self.fallback = reason
        self.model = None
        gc.collect()
        if torch.cuda.is_initialized():
            torch.cuda.empty_cache()
        log.warning('CUDA fallback to CPU FP32: %s', reason)
        self._load('cpu')

    def _ensure(self):
        if self.model is not None:
            return
        import torch
        if self.config.device == 'cpu':
            return self._load('cpu')
        try:
            available = torch.cuda.is_available()
            if available:
                torch.cuda.init()
        except (RuntimeError, OSError) as exc:
            if self.config.device == 'cuda':
                raise RagError(f'Explicit CUDA initialization failed: {exc}') from exc
            return self._cpu(f'CUDA initialization failed: {exc}')
        if not available:
            if self.config.device == 'cuda':
                raise RagError('Explicit CUDA requested, but this PyTorch wheel/driver has no available CUDA device')
            return self._cpu('CUDA unavailable')
        try:
            self._load('cuda')
        except torch.cuda.OutOfMemoryError:
            if self.config.device == 'cuda':
                raise
            self._cpu('GPU model loading ran out of memory')
        # Other model/configuration failures deliberately propagate.

    def encode(self, texts, query=False, batch_size=4):
        if not texts:
            return np.empty((0, 768), dtype=np.float32)
        self._ensure()
        import torch

        def run(size):
            return self.model.encode(texts, batch_size=size, prompt_name='SearchQuery' if query else None,
                                     normalize_embeddings=True, convert_to_numpy=True,
                                     show_progress_bar=False)
        try:
            result = run(batch_size)
        except torch.cuda.OutOfMemoryError:
            if self.device != 'cuda':
                raise
            gc.collect()
            torch.cuda.empty_cache()
            log.warning('CUDA OOM; retrying whole request once with batch_size=%s', max(1, batch_size // 2))
            try:
                result = run(max(1, batch_size // 2))
            except torch.cuda.OutOfMemoryError:
                if self.config.device == 'cuda':
                    raise RagError('Explicit CUDA: OOM after one smaller-batch retry; select cpu or reduce input')
                self._cpu('OOM after one smaller-batch retry')
                result = run(max(1, batch_size // 2))
        result = np.asarray(result, dtype=np.float32)
        if result.shape != (len(texts), 768) or not np.isfinite(result).all():
            raise RagError('Model produced invalid dimensions or NaN/Inf')
        norms = np.linalg.norm(result, axis=1, keepdims=True)
        if np.any(norms < 1e-12):
            raise RagError('Model produced a zero embedding')
        # BF16 pooling/normalization is rounded; finalize the L2 norm in FP32.
        return validate_vectors(result / norms, len(texts))

    def status(self):
        return {'loaded': self.model is not None, 'device': self.device, 'dtype': self.dtype,
                'fallback_reason': self.fallback, 'vision': self.vision}
