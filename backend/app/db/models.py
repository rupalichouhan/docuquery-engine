import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(64), nullable=False, default="application/pdf")
    total_pages = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="PENDING")  # PENDING, PARSING, CHUNKING, EXTRACTING, INDEXING, COMPLETED, FAILED
    current_step = Column(String(64), nullable=False, default="Waiting in queue")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    bounding_box = Column(JSON, nullable=True)  # { "x0": ..., "y0": ..., "x1": ..., "y1": ... }
    tables_extracted = Column(JSON, nullable=True)  # Markdown / tabular structures
    embedding = Column(JSON, nullable=True)  # List[float] (384 floats), portable across Postgres & SQLite
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="chunks")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    citations = Column(JSON, nullable=False)
    verification_results = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
