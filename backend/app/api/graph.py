from typing import List, Optional
from fastapi import APIRouter, Query
from app.graph.kuzu_client import graph_db

router = APIRouter(prefix="/api/v1/graph", tags=["Knowledge Graph"])


@router.get("/explore")
async def explore_graph(
    entity: str = Query(..., min_length=1, description="Entity name to explore"),
    max_hops: int = Query(default=2, ge=1, le=3),
):
    """Returns 1-to-2 hop knowledge subgraph around a requested entity."""
    return graph_db.query_neighborhood([entity], max_hops=max_hops)
