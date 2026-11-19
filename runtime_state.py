"""Shared runtime coordination for SVC and separation models.

Kept deliberately import-light: the separation path needs the same lock and
CUDA cleanup, but must not import my_inference (torch, transformers, HF env
setup) just to free memory.
"""

import gc
import threading
from contextlib import contextmanager


MODEL_CACHE = {}
MODEL_RUNTIME_LOCK = threading.RLock()


def _empty_cuda_cache():
    try:
        import torch
    except Exception:
        return
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def clear_cached_models_locked():
    """Drop cached model bundles. Caller must hold MODEL_RUNTIME_LOCK."""
    MODEL_CACHE.clear()
    # Dropping the last reference frees the weights; collect before asking
    # CUDA to release the now-unused blocks.
    gc.collect()
    _empty_cuda_cache()


@contextmanager
def model_runtime(release_cache=False):
    """Serialize model loading/inference across UI events.

    release_cache=True evicts the cached SVC bundle first, so separation can
    have the whole GPU. SVC reloads lazily on its next run.
    """
    with MODEL_RUNTIME_LOCK:
        if release_cache:
            clear_cached_models_locked()
        yield
