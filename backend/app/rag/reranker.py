import os
import time
from typing import List, Dict, Any
from flashrank import Ranker, RerankRequest
from app.core.config import settings
from app.core.logging import logger

FLASHRANK_CACHE_DIR = os.path.abspath("./data/models/flashrank")


class LocalFlashReranker:
    """Local CPU cross-encoder reranker powered by FlashRank."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalFlashReranker, cls).__new__(cls)
            logger.info(f"Initializing FlashRank model: {settings.RERANKER_MODEL} from {FLASHRANK_CACHE_DIR}")
            cls._instance.ranker = Ranker(
                model_name=settings.RERANKER_MODEL,
                cache_dir=FLASHRANK_CACHE_DIR,
            )
        return cls._instance

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5) -> Dict[str, Any]:
        """
        Reranks candidate chunks with FlashRank.
        Returns top_k chunks with their cross-encoder score and rerank latency.
        """
        if not chunks:
            return {"reranked_chunks": [], "latency_ms": 0}

        start_time = time.time()
        passages = [
            {"id": c["chunk_id"], "text": c["content"], "meta": c}
            for c in chunks
        ]

        rerank_req = RerankRequest(query=query, passages=passages)
        ranked_results = self.ranker.rerank(rerank_req)

        reranked_chunks = []
        for r in ranked_results[:top_k]:
            original_meta = r["meta"]
            original_meta["rerank_score"] = float(r["score"])
            reranked_chunks.append(original_meta)

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"FlashRank reranked {len(chunks)} chunks down to {len(reranked_chunks)} in {latency_ms}ms")

        return {
            "reranked_chunks": reranked_chunks,
            "latency_ms": latency_ms,
        }


reranker = LocalFlashReranker()
