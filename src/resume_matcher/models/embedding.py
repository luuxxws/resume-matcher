# src/resume_matcher/models/embedding.py

import logging
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

from ..config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_CACHE_DIR,
    DEVICE,
)

logger = logging.getLogger(__name__)

try:
    model = SentenceTransformer(
        EMBEDDING_MODEL_NAME,
        device=DEVICE,
        trust_remote_code=True,
    )
    logger.info(f"Loaded embedding model: {EMBEDDING_MODEL_NAME} on {DEVICE}")
except Exception as e:
    logger.error(f"Failed to load embedding model: {e}")
    raise

DIMENSION = model.get_sentence_embedding_dimension()
logger.info(f"Embedding dimension: {DIMENSION}")


def get_embedding(
        text: str,
        normalize: bool = True,
        batch_size: int = 1,
) -> np.ndarray:
    """
    Generates embedding for a single text.
    Returns an np.ndarray of size (DIMENSION)
    """
    if not text or not text.strip():
        logger.warning("Empty text for embedding -> returning zero vector")
        return np.zeros(DIMENSION, dtype=np.float32)

    embedding = model.encode(
        text,
        normalize_embeddings=normalize,
        batch_size=batch_size,
        show_progress_bar=False,
    )
    return embedding.astype(np.float32)


def batch_get_embeddings(
        texts: List[str],
    normalize: bool = True,
    batch_size: int = 32,
) -> np.ndarray:
    """
    Generates embeddings for a list of texts.
    Returns an np.ndarray of size (len(texts), DIMENSION)
    """
    if not texts:
        return np.array([], dtype=np.float32).reshape(0, DIMENSION)
    
    cleaned_texts = [t if t and t.strip() else "" for t in texts]

    embeddings = model.encode(
        cleaned_texts,
        normalize_embeddings=normalize,
        batch_size=batch_size,
        show_progress_bar=True,
    )

    for i, text in enumerate(cleaned_texts):
        if not text.strip():
            embeddings[i] = 0.0

    return embeddings.astype(np.float32)


# –– Caching based on file –––––––––––––––––––––––––––––––––––––––––––––––––––––

def get_cached_embedding(file_path: Union[str, Path]) -> Optional[np.ndarray]:
    """Attempts to load embedding from cache"""
    cache_path = EMBEDDING_CACHE_DIR / f"{Path(file_path).stem}.pkl"
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                emb = pickle.load(f)
            if emb.shape == (DIMENSION,):
                logger.debug(f"Loaded cached embedding for {file_path}")
                return emb
        except Exception as e:
            logger.warning(f"Failed to load cache {cache_path}: {e}")
    return None


def save_embedding_to_cache(file_path: Union[str, Path], embedding: np.ndarray):
    """Saves embedding in cache"""
    EMBEDDING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = EMBEDDING_CACHE_DIR / f"{Path(file_path).stem}.pkl"
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(embedding, f)
        logger.debug(f"Saved embedding cache: {cache_path}")
    except Exception as e:
        logger.warning(f"Failed to save cache {cache_path}: {e}")


def get_or_compute_embedding(
    text: str,
    file_path: Optional[Union[str, Path]] = None,
    force_recompute: bool = False,
) -> np.ndarray:
    """
    Smart method: takes from cache if available and does not force_recompute,
    otherwise calculates and saves to cache.
    """
    if file_path and not force_recompute:
        cached = get_cached_embedding(file_path)
        if cached is not None:
            return cached

    emb = get_embedding(text)
    
    if file_path:
        save_embedding_to_cache(file_path, emb)
    
    return emb