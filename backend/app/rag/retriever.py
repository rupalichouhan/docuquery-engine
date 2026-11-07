from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import DocumentChunk, Document
from app.graph.kuzu_client import graph_db
from app.ingestion.embedder import embedder
from app.ingestion.extractor import extractor
from app.core.logging import logger


class HybridRetriever:
    """Hybrid Retriever combining dense vector similarity with KùzuDB graph traversal via RRF."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        session: Session,
        document_ids: Optional[List[str]] = None,
        vector_top_k: int = 20,
        graph_top_k: int = 20,
        fused_top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval:
        1. Dense vector search
        2. Graph traversal from query entities
        3. Reciprocal Rank Fusion (RRF)
        """
        # 1. Vector Search
        query_vector = embedder.embed_query(query)
        
        # Load candidate chunks from DB
        stmt = select(DocumentChunk, Document.title).join(Document, DocumentChunk.document_id == Document.id)
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
        
        chunks_with_doc = session.execute(stmt).all()

        vector_ranked = []
        for chunk, doc_title in chunks_with_doc:
            if not chunk.embedding:
                continue
            sim = embedder.cosine_similarity(query_vector, chunk.embedding)
            vector_ranked.append({
                "chunk": chunk,
                "doc_title": doc_title,
                "score": sim,
            })

        vector_ranked.sort(key=lambda x: x["score"], reverse=True)
        top_vector_results = vector_ranked[:vector_top_k]

        # 2. Graph Traversal Search
        query_entities = extractor.extract_local_entities(query)
        entity_names = [e["name"] for e in query_entities]
        
        query_words = [w.strip() for w in query.split() if len(w) > 3 and w[0].isupper()]
        probe_entities = list(set(entity_names + query_words))

        graph_chunk_ids = graph_db.get_connected_chunks(probe_entities, limit=graph_top_k)
        
        graph_ranked = []
        if graph_chunk_ids:
            g_stmt = (
                select(DocumentChunk, Document.title)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.id.in_(graph_chunk_ids))
            )
            if document_ids:
                g_stmt = g_stmt.where(DocumentChunk.document_id.in_(document_ids))
            
            for chunk, doc_title in session.execute(g_stmt).all():
                graph_ranked.append({
                    "chunk": chunk,
                    "doc_title": doc_title,
                })

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        # Add vector rankings
        for rank, item in enumerate(top_vector_results, start=1):
            c_id = item["chunk"].id
            chunk_map[c_id] = item
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.rrf_k + rank))

        # Add graph rankings
        for rank, item in enumerate(graph_ranked, start=1):
            c_id = item["chunk"].id
            if c_id not in chunk_map:
                chunk_map[c_id] = item
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (self.rrf_k + rank))

        # Sort by final RRF score
        fused_items = []
        for c_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:fused_top_k]:
            data = chunk_map[c_id]
            fused_items.append({
                "chunk_id": c_id,
                "document_id": data["chunk"].document_id,
                "doc_title": data["doc_title"],
                "page_number": data["chunk"].page_number,
                "content": data["chunk"].content,
                "bounding_box": data["chunk"].bounding_box,
                "tables_extracted": data["chunk"].tables_extracted or [],
                "rrf_score": score,
            })

        logger.info(
            f"Retrieval complete for '{query}': {len(top_vector_results)} vector hits, "
            f"{len(graph_ranked)} graph hits, fused into {len(fused_items)} top chunks."
        )

        return {
            "fused_chunks": fused_items,
            "seed_entities": probe_entities,
            "vector_hits_count": len(top_vector_results),
            "graph_hits_count": len(graph_ranked),
        }


retriever = HybridRetriever()
