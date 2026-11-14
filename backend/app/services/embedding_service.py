import hashlib
import math
from typing import List
import numpy as np

from app.config import settings
from app.utils.logger import logger


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
    Generate a 768-dimensional semantic embedding for the provided text.
    Uses Google text-embedding-004 when API key is set, falling back gracefully
    to deterministic projection.
    """
    cleaned = text.strip()
    if not cleaned:
        return [0.0] * 768

    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=cleaned,
            )
            if response.embedding and hasattr(response.embedding, "values"):
                return list(response.embedding.values)
        except Exception as e:
            logger.warning(f"Gemini embedding API call failed: {e}. Falling back to local embedding.")

    return generate_deterministic_embedding(cleaned, dim=768)


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
