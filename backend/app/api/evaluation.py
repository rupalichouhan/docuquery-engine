from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.evaluation.evaluator import evaluator
from app.rag.engine import rag_engine

router = APIRouter(prefix="/api/v1/evaluation", tags=["RAG Evaluation"])


@router.post("/run")
def run_evaluation(session: Session = Depends(get_db)):
    """Triggers quantitative evaluation of the 15-question benchmark dataset."""
    results = evaluator.run_benchmark(rag_engine, session)
    return results
