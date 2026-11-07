import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.rag.retriever import retriever
from app.rag.reranker import reranker
from app.verification.ast_verifier import verifier
from app.llm.gemini import llm_provider
from app.graph.kuzu_client import graph_db
from app.db.models import QueryLog
from app.core.logging import logger


class RAGEngine:
    """Unified Orchestrator for DocuQuery Engine's Hybrid Graph-RAG Pipeline."""

    def execute_query(
        self,
        query: str,
        session: Session,
        document_ids: Optional[List[str]] = None,
        verify_math: bool = True,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        overall_start = time.time()

        # 1. Hybrid Retrieval (Vector + Graph + RRF)
        retrieval_res = retriever.retrieve(
            query=query,
            session=session,
            document_ids=document_ids,
            vector_top_k=15,
            graph_top_k=15,
            fused_top_k=10,
        )
        fused_chunks = retrieval_res["fused_chunks"]
        seed_entities = retrieval_res["seed_entities"]

        # 2. Local FlashRank Reranking
        rerank_res = reranker.rerank(
            query=query,
            chunks=fused_chunks,
            top_k=top_k,
        )
        final_context_chunks = rerank_res["reranked_chunks"]
        rerank_ms = rerank_res["latency_ms"]

        # 3. Grounded LLM Generation
        generation_res = llm_provider.generate_grounded_answer(
            query=query,
            context_chunks=final_context_chunks,
        )
        answer = generation_res["answer"]
        citations = generation_res["citations"]

        # 4. AST Deterministic Numerical Verification
        verification_badges = []
        if verify_math and final_context_chunks:
            verification_badges = verifier.scan_and_verify_response(
                answer_text=answer,
                context_chunks=final_context_chunks,
            )

        # 5. Extract Related Knowledge Subgraph for UI rendering
        graph_subgraph = graph_db.query_neighborhood(seed_entities, max_hops=2)

        total_latency_ms = int((time.time() - overall_start) * 1000)

        # 6. Telemetry & Metrics
        metrics = {
            "total_latency_ms": total_latency_ms,
            "rerank_latency_ms": rerank_ms,
            "vector_candidates": retrieval_res["vector_hits_count"],
            "graph_candidates": retrieval_res["graph_hits_count"],
            "context_chunks_used": len(final_context_chunks),
            "verification_count": len(verification_badges),
            "graph_nodes_count": len(graph_subgraph.get("nodes", [])),
            "graph_edges_count": len(graph_subgraph.get("edges", [])),
        }

        # 7. Audit Logging in DB
        try:
            from app.db.session import SessionLocal
            with SessionLocal() as log_session:
                log_entry = QueryLog(
                    query_text=query,
                    response_text=answer,
                    citations=citations,
                    verification_results=verification_badges,
                    metrics=metrics,
                    latency_ms=total_latency_ms,
                )
                log_session.add(log_entry)
                log_session.commit()
        except Exception as e:
            logger.warning(f"Could not persist query audit log: {e}")

        return {
            "answer": answer,
            "citations": citations,
            "verification": verification_badges,
            "graph_subgraph": graph_subgraph,
            "metrics": metrics,
            "context_chunks": [
                {
                    "chunk_id": c["chunk_id"],
                    "doc_title": c["doc_title"],
                    "page_number": c["page_number"],
                    "rerank_score": c.get("rerank_score", 0.0),
                    "content": c["content"],
                }
                for c in final_context_chunks
            ],
        }


rag_engine = RAGEngine()
