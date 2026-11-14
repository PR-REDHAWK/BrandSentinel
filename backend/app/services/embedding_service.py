import hashlib
import math
from typing import List
import numpy as np

from app.config import settings
from app.utils.logger import logger

# In-memory LRU embedding cache (text hash -> vector)
_EMBEDDING_CACHE: dict = {}
_MAX_CACHE_SIZE = 1024


def generate_deterministic_embedding(text: str, dim: int = 768) -> List[float]:
    """
    Generate a deterministic normalized float vector of specified dimension
    based on character and token n-gram hashing.
    """
    vec = np.zeros(dim, dtype=np.float32)
    words = text.lower().split()
    if not words:
        return vec.tolist()

    for idx, word in enumerate(words):
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        pos = h % dim
        sign = 1.0 if ((h >> 8) & 1) else -1.0
        weight = 1.0 / math.sqrt(idx + 1)
        vec[pos] += sign * weight

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def get_embedding(text: str) -> List[float]:
    """
    Generate a semantic embedding for the provided text.
    Uses in-memory LRU cache and Google text-embedding-004 when API key is set,
    falling back gracefully to deterministic projection.
    """
    cleaned = text.strip()
    if not cleaned:
        return [0.0] * 768

    cache_key = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
    if cache_key in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[cache_key]

    embedding_vec: List[float] = []

    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=cleaned,
            )
            if hasattr(response, "embeddings") and response.embeddings:
                embedding_vec = list(response.embeddings[0].values)
            elif hasattr(response, "embedding") and response.embedding and hasattr(response.embedding, "values"):
                embedding_vec = list(response.embedding.values)
        except Exception as e:
            logger.warning(f"Gemini embedding API call failed: {e}. Falling back to local embedding.")

    if not embedding_vec:
        embedding_vec = generate_deterministic_embedding(cleaned, dim=768)

    # Cache eviction if full
    if len(_EMBEDDING_CACHE) >= _MAX_CACHE_SIZE:
        _EMBEDDING_CACHE.pop(next(iter(_EMBEDDING_CACHE)))
    _EMBEDDING_CACHE[cache_key] = embedding_vec

    return embedding_vec


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Batch generate embeddings for multiple text passages."""
    return [get_embedding(t) for t in texts]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
