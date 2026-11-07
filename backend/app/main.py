from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db
from app.api import documents, query, graph, evaluation


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB schema
    logger.info("Initializing DocuQuery Engine backend services...")
    init_db()
    logger.info("All backend services initialized.")
    yield
    # Shutdown
    logger.info("Shutting down DocuQuery Engine...")


app = FastAPI(
    title="DocuQuery Engine API",
    description="Portfolio-grade Hybrid Graph-RAG & Document Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(graph.router)
app.include_router(evaluation.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "engine": "DocuQuery Engine",
        "environment": settings.ENVIRONMENT,
        "embedding_model": settings.EMBEDDING_MODEL,
        "reranker_model": settings.RERANKER_MODEL,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
