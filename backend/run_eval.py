import json
import os
from app.db.session import SessionLocal, init_db
from app.rag.engine import rag_engine
from app.evaluation.evaluator import evaluator
from app.core.logging import logger

def main():
    logger.info("Initializing database for benchmark run...")
    init_db()
    
    with SessionLocal() as session:
        logger.info("Executing 15-question quantitative RAG evaluation benchmark...")
        summary = evaluator.run_benchmark(rag_engine, session)
        
        print("\n" + "=" * 60)
        print("DOCUQUERY ENGINE - QUANTITATIVE RAG BENCHMARK RESULTS")
        print("=" * 60)
        print(f"Total Benchmark Questions:   {summary['total_benchmark_questions']}")
        print(f"Average Context Precision:   {summary['average_context_precision'] * 100:.1f}%")
        print(f"Average Faithfulness:       {summary['average_faithfulness'] * 100:.1f}%")
        print(f"Average Answer Relevance:   {summary['average_answer_relevance'] * 100:.1f}%")
        print(f"Math Verification Accuracy: {summary['math_verification_accuracy'] * 100:.1f}%")
        print("=" * 60)
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "benchmark_results.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"Detailed results persisted to {output_file}")

if __name__ == "__main__":
    main()
