import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.core.logging import logger
from app.db.models import Document, DocumentChunk
from app.graph.kuzu_client import graph_db
from app.ingestion.parser import PDFDocumentParser
from app.ingestion.chunker import SemanticChunker
from app.ingestion.embedder import embedder
from app.ingestion.extractor import extractor


class DocumentIngestionPipeline:
    """End-to-end ingestion orchestrator for DocuQuery Engine with granular progress states."""

    def __init__(self):
        self.parser = PDFDocumentParser()
        self.chunker = SemanticChunker()

    def process_document(self, doc_id: str, file_path: str, session: Session) -> Dict[str, Any]:
        logger.info(f"Starting ingestion pipeline for document: {doc_id} at {file_path}")

        try:
            # 1. Parsing Phase
            session.execute(
                update(Document).where(Document.id == doc_id).values(status="PARSING", current_step="Parsing PDF")
            )
            session.commit()

            parsed = self.parser.parse(file_path)
            total_pages = parsed["total_pages"]

            # 2. Chunking Phase
            session.execute(
                update(Document).where(Document.id == doc_id).values(status="CHUNKING", current_step="Chunking Text", total_pages=total_pages)
            )
            session.commit()

            chunks = self.chunker.chunk_document(parsed)
            logger.info(f"Document {doc_id} produced {len(chunks)} semantic chunks across {total_pages} pages.")

            if not chunks:
                raise ValueError("No text or content could be extracted from the document.")

            # 3. Entity & Edge Extraction Phase
            session.execute(
                update(Document).where(Document.id == doc_id).values(status="EXTRACTING", current_step="Extracting Entities")
            )
            session.commit()

            chunk_texts = [c["content"] for c in chunks]
            embeddings = embedder.embed_texts(chunk_texts)

            # 4. Indexing Phase (Vectors in SQL & Property Graph in KùzuDB)
            session.execute(
                update(Document).where(Document.id == doc_id).values(status="INDEXING", current_step="Indexing")
            )
            session.commit()

            for idx, c in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_embedding = embeddings[idx]

                local_entities = extractor.extract_local_entities(c["content"])
                relations = extractor._local_relation_heuristics(c["content"], local_entities)

                db_chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                    content=c["content"],
                    bounding_box=c.get("bounding_box"),
                    tables_extracted=c.get("tables_extracted"),
                    embedding=chunk_embedding,
                )
                session.add(db_chunk)

                graph_db.add_chunk_and_entities(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    page_number=c["page_number"],
                    entities=local_entities,
                    relations=relations,
                )

            # 5. Completed
            session.execute(
                update(Document)
                .where(Document.id == doc_id)
                .values(status="COMPLETED", current_step="Completed", total_pages=total_pages, error_message=None)
            )
            session.commit()

            logger.info(f"Ingestion successfully completed for document: {doc_id}")
            return {"status": "COMPLETED", "chunks_count": len(chunks), "pages": total_pages}

        except Exception as e:
            logger.error(f"Ingestion failed for document {doc_id}: {e}", exc_info=True)
            session.rollback()
            session.execute(
                update(Document)
                .where(Document.id == doc_id)
                .values(status="FAILED", current_step="Failed", error_message=str(e))
            )
            session.commit()
            return {"status": "FAILED", "error": str(e)}


pipeline = DocumentIngestionPipeline()
