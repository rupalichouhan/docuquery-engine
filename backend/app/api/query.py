from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.rag.engine import rag_engine
from app.core.security import rate_limiter

router = APIRouter(prefix="/api/v1/query", tags=["Query"])


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="User search or research query")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional scope of documents")
    verify_math: bool = Field(default=True, description="Enable deterministic AST arithmetic verification")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to use")


@router.post("")
def execute_query(
    request: Request,
    payload: QueryRequest,
    session: Session = Depends(get_db),
):
    """Executes Hybrid Graph-RAG query with AST numerical verification and citation tracking."""
    rate_limiter.check(request)
    
    res = rag_engine.execute_query(
        query=payload.query,
        session=session,
        document_ids=payload.document_ids,
        verify_math=payload.verify_math,
        top_k=payload.top_k,
    )
    return res
