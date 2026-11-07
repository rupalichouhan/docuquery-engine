from typing import List
import numpy as np
from fastembed import TextEmbedding
from app.core.config import settings
from app.core.logging import logger


class FastEmbedder:
    """Generates dense embeddings locally via FastEmbed on CPU."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FastEmbedder, cls).__new__(cls)
            logger.info(f"Initializing FastEmbed model: {settings.EMBEDDING_MODEL}")
            cls._instance.model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
        return cls._instance

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a batch of texts."""
        if not texts:
            return []
        embeddings = list(self.model.embed(texts))
        return [e.tolist() for e in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """Compute embedding for a single search query."""
        res = list(self.model.embed([query]))
        return res[0].tolist()

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vector lists."""
        a = np.array(v1, dtype=np.float32)
        b = np.array(v2, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


embedder = FastEmbedder()
