import pytest
from app.verification.ast_verifier import verifier, SafeASTCalculator
from app.ingestion.embedder import embedder
from app.graph.kuzu_client import graph_db
from app.ingestion.chunker import SemanticChunker
from app.rag.retriever import retriever
from app.rag.reranker import reranker
from app.evaluation.evaluator import evaluator


def test_safe_ast_calculator_basic_ops():
    # Basic arithmetic
    assert SafeASTCalculator.evaluate("10 + 5") == 15.0
    assert SafeASTCalculator.evaluate("100 - 25.5") == 74.5
    assert SafeASTCalculator.evaluate("12 * 8") == 96.0
    assert SafeASTCalculator.evaluate("50 / 2") == 25.0
    # Nested formula for growth rate
    assert SafeASTCalculator.evaluate("((115 - 100) / 100) * 100") == 15.0


def test_safe_ast_calculator_rejects_unsafe():
    with pytest.raises(Exception):
        SafeASTCalculator.evaluate("__import__('os').system('ls')")
    with pytest.raises(Exception):
        SafeASTCalculator.evaluate("open('file.txt')")


def test_ast_numerical_verifier_success():
    res = verifier.verify_claim(
        claim_description="Revenue growth from 2023 to 2024",
        claimed_value=15.0,
        formula_expr="((115 - 100) / 100) * 100",
        table_context="| Metric | 2023 | 2024 |\n| Revenue | 100 | 115 |",
    )
    assert res["is_verified"] is True
    assert res["badge"] == "Verified Calculation"
    assert res["calculated_value"] == 15.0


def test_ast_numerical_verifier_discrepancy():
    res = verifier.verify_claim(
        claim_description="Operating income growth",
        claimed_value=30.0,  # Claim says 30%
        formula_expr="((115 - 100) / 100) * 100",  # Actually 15%
    )
    assert res["is_verified"] is False
    assert res["badge"] == "Calculation Discrepancy"
    assert "differs" in res["details"]


def test_fastembed_local_embeddings():
    v1 = embedder.embed_query("Machine learning optimization")
    v2 = embedder.embed_query("Deep neural network training")
    v3 = embedder.embed_query("Financial balance sheet quarterly report")

    assert len(v1) == 384
    assert len(v2) == 384
    assert len(v3) == 384

    sim_ai = embedder.cosine_similarity(v1, v2)
    sim_fin = embedder.cosine_similarity(v1, v3)
    assert sim_ai > sim_fin  # AI query should be closer to AI than financial report


def test_semantic_chunker_table_preservation():
    chunker = SemanticChunker(target_chunk_words=100)
    mock_doc = {
        "pages": [
            {
                "page_number": 1,
                "text": "Executive Summary\n\nOur fiscal year concluded with solid performance.",
                "tables": [
                    {
                        "markdown": "| Revenue | Net Income |\n| --- | --- |\n| $100M | $25M |",
                        "raw_rows": [["Revenue", "Net Income"], ["$100M", "$25M"]],
                    }
                ],
                "bounding_box": {"x0": 0, "top": 0, "x1": 500, "bottom": 700},
            }
        ]
    }
    chunks = chunker.chunk_document(mock_doc)
    assert len(chunks) >= 2
    # Check table chunk
    table_chunk = next(c for c in chunks if c["metadata"]["type"] == "table")
    assert "$100M" in table_chunk["content"]
    assert table_chunk["tables_extracted"]


def test_kuzu_graph_manager():
    doc_id = "test_doc_001"
    chunk_id = "test_chunk_001"
    entities = [
        {"name": "Apple Inc", "category": "COMPANY"},
        {"name": "Revenue", "category": "METRIC"},
    ]
    relations = [
        {
            "source": "Apple Inc",
            "target": "Revenue",
            "relation_type": "REPORTED_VALUE",
            "evidence": "Apple reported revenue of $85B",
        }
    ]

    graph_db.add_chunk_and_entities(chunk_id, doc_id, 1, entities, relations)
    neighborhood = graph_db.query_neighborhood(["Apple Inc"], max_hops=1)
    
    assert any(n["id"] == "Apple Inc" for n in neighborhood["nodes"])
    assert any(e["source"] == "Apple Inc" and e["target"] == "Revenue" for e in neighborhood["edges"])

    # Test cascade delete
    graph_db.delete_document_subgraph(doc_id)
    connected = graph_db.get_connected_chunks(["Apple Inc"])
    assert chunk_id not in connected


def test_flashrank_reranker():
    query = "financial revenue and income"
    mock_chunks = [
        {"chunk_id": "c1", "content": "Weather forecast for sunny tomorrow."},
        {"chunk_id": "c2", "content": "The company reported quarterly revenue of 100 million and operating income of 25 million."},
    ]
    reranked = reranker.rerank(query, mock_chunks, top_k=2)
    assert len(reranked["reranked_chunks"]) == 2
    # The financial chunk should be ranked first
    assert reranked["reranked_chunks"][0]["chunk_id"] == "c2"
    assert "rerank_score" in reranked["reranked_chunks"][0]


def test_rag_evaluation_metrics():
    # Context precision test
    ctx = ["Revenue was $100M in 2023 and increased to $115M in 2024."]
    prec = evaluator.evaluate_context_precision(ctx, "Revenue was $100M in 2023 and increased to $115M in 2024.")
    assert prec == 1.0

    # Faithfulness test
    answer = "Revenue increased to $115M in 2024."
    faith = evaluator.evaluate_faithfulness(answer, ctx[0])
    assert faith > 0.5
