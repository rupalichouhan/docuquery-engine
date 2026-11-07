import json
import os
import re
from typing import List, Dict, Any
from app.ingestion.embedder import embedder
from app.verification.ast_verifier import verifier
from app.core.logging import logger


class RAGEvaluator:
    """Evaluates RAG pipeline against golden benchmarks."""

    def __init__(self, benchmark_file: str = "app/evaluation/benchmark_data.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "benchmark_data.json")
        with open(path, "r", encoding="utf-8") as f:
            self.benchmark_dataset = json.load(f)

    def evaluate_context_precision(self, retrieved_contexts: List[str], expected_context: str) -> float:
        """Precision: Fraction of retrieved context chunks that contain key expected terms."""
        if not retrieved_contexts or not expected_context:
            return 0.0

        keywords = [w.lower() for w in re.findall(r"\w+", expected_context) if len(w) > 3]
        if not keywords:
            return 1.0

        hits = 0
        for ctx in retrieved_contexts:
            ctx_lower = ctx.lower()
            matching_kw = sum(1 for kw in keywords if kw in ctx_lower)
            if matching_kw / len(keywords) >= 0.3:
                hits += 1

        return round(hits / len(retrieved_contexts), 3)

    def evaluate_faithfulness(self, answer: str, context: str) -> float:
        """Faithfulness: Fraction of statements in answer directly verifiable against context."""
        sentences = [s.strip() for s in re.split(r"[.!?\n]", answer) if len(s.strip()) > 15]
        if not sentences:
            return 1.0

        context_lower = context.lower()
        faithful_count = 0
        for sent in sentences:
            words = [w.lower() for w in re.findall(r"\w+", sent) if len(w) > 3]
            if not words:
                continue
            matches = sum(1 for w in words if w in context_lower)
            if (matches / len(words)) >= 0.4:
                faithful_count += 1

        return round(faithful_count / len(sentences), 3)

    def evaluate_answer_relevance(self, query: str, answer: str) -> float:
        """Semantic cosine similarity between question and answer."""
        if not answer.strip():
            return 0.0
        q_vec = embedder.embed_query(query)
        a_vec = embedder.embed_query(answer[:300])
        sim = embedder.cosine_similarity(q_vec, a_vec)
        return round(max(0.0, min(1.0, (sim + 1.0) / 2.0)), 3)

    def run_benchmark(self, rag_engine_instance, session) -> Dict[str, Any]:
        """Runs the 15-question benchmark test suite."""
        results = []
        total_prec = 0.0
        total_faith = 0.0
        total_relevance = 0.0
        math_checks_passed = 0
        math_checks_total = 0

        for idx, item in enumerate(self.benchmark_dataset, start=1):
            q = item["question"]
            exp_ctx = item["expected_context"]
            logger.info(f"[{idx}/{len(self.benchmark_dataset)}] Benchmark query: {q[:50]}...")

            # Query the engine synchronously
            res = rag_engine_instance.execute_query(
                query=q,
                session=session,
                verify_math=item.get("requires_math_verification", False),
                top_k=3,
            )

            retrieved_texts = [c["content"] for c in res.get("context_chunks", [])]
            combined_ctx = "\n".join(retrieved_texts)

            prec = self.evaluate_context_precision(retrieved_texts, exp_ctx)
            faith = self.evaluate_faithfulness(res["answer"], combined_ctx)
            relevance = self.evaluate_answer_relevance(q, res["answer"])

            total_prec += prec
            total_faith += faith
            total_relevance += relevance

            if item.get("requires_math_verification"):
                math_checks_total += 1
                if res.get("verification") and any(v.get("is_verified") for v in res["verification"]):
                    math_checks_passed += 1

            results.append({
                "id": item["id"],
                "question": q,
                "answer": res["answer"],
                "precision": prec,
                "faithfulness": faith,
                "relevance": relevance,
                "verification_badges": res.get("verification", []),
            })

        n = len(self.benchmark_dataset)
        summary = {
            "total_benchmark_questions": n,
            "average_context_precision": round(total_prec / n, 3),
            "average_faithfulness": round(total_faith / n, 3),
            "average_answer_relevance": round(total_relevance / n, 3),
            "math_verification_accuracy": (
                round(math_checks_passed / math_checks_total, 3) if math_checks_total else 1.0
            ),
            "benchmark_results": results,
        }
        return summary


evaluator = RAGEvaluator()
