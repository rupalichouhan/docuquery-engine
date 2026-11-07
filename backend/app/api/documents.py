import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import List, Dict, Any

from app.core.config import settings
from app.core.logging import logger
from app.core.security import validate_pdf_upload, sanitize_filename
from app.db.session import get_db, SessionLocal
from app.db.models import Document, DocumentChunk
from app.graph.kuzu_client import graph_db
from app.ingestion.pipeline import pipeline

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
):
    """Securely uploads and queues a PDF for background processing."""
    file_bytes = await validate_pdf_upload(file)
    clean_name = sanitize_filename(file.filename)
    doc_id = str(uuid.uuid4())
    save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{clean_name}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # Create pending Document record
    new_doc = Document(
        id=doc_id,
        title=clean_name.replace(".pdf", "").replace("_", " ").title(),
        filename=clean_name,
        file_path=save_path,
        file_size_bytes=len(file_bytes),
        mime_type="application/pdf",
        status="PENDING",
    )
    session.add(new_doc)
    session.commit()
    session.refresh(new_doc)

    # Process in background with a dedicated session
    def run_ingestion(d_id: str, f_path: str):
        try:
            with SessionLocal() as bg_session:
                pipeline.process_document(d_id, f_path, bg_session)
        except Exception as e:
            logger.error(f"Background ingestion task exception for {d_id}: {e}", exc_info=True)
            try:
                with SessionLocal() as err_session:
                    err_session.execute(
                        update(Document)
                        .where(Document.id == d_id)
                        .values(status="FAILED", current_step="Failed", error_message=str(e))
                    )
                    err_session.commit()
            except Exception as db_err:
                logger.error(f"Failed to record failure status for {d_id}: {db_err}")

    background_tasks.add_task(run_ingestion, doc_id, save_path)

    return {
        "id": new_doc.id,
        "title": new_doc.title,
        "filename": new_doc.filename,
        "file_size_bytes": new_doc.file_size_bytes,
        "status": new_doc.status,
        "message": "Document uploaded successfully and ingestion queued.",
    }


@router.get("", response_model=List[Dict[str, Any]])
def list_documents(session: Session = Depends(get_db)):
    """List all documents with their ingestion statuses."""
    docs = session.execute(select(Document).order_by(Document.created_at.desc())).scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "filename": d.filename,
            "file_size_bytes": d.file_size_bytes,
            "total_pages": d.total_pages,
            "status": d.status,
            "current_step": getattr(d, "current_step", "Waiting in queue"),
            "error_message": d.error_message,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/{doc_id}")
def get_document(doc_id: str, session: Session = Depends(get_db)):
    """Get single document details."""
    doc = session.execute(select(Document).where(Document.id == doc_id)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "title": doc.title,
        "filename": doc.filename,
        "file_size_bytes": doc.file_size_bytes,
        "total_pages": doc.total_pages,
        "status": doc.status,
        "current_step": getattr(doc, "current_step", "Waiting in queue"),
        "error_message": doc.error_message,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/{doc_id}/file")
def get_document_file(doc_id: str, session: Session = Depends(get_db)):
    """Stream PDF inline for browser viewing without triggering unintended download prompts."""
    doc = session.execute(select(Document).where(Document.id == doc_id)).scalar_one_or_none()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")
    return FileResponse(
        path=doc.file_path,
        media_type="application/pdf",
        content_disposition_type="inline",
        filename=doc.filename,
        headers={
            "Content-Disposition": f'inline; filename="{doc.filename}"',
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.delete("/{doc_id}")
def delete_document(doc_id: str, session: Session = Depends(get_db)):
    """Hard-delete document across Postgres, vector store, KùzuDB, and disk storage."""
    doc = session.execute(select(Document).where(Document.id == doc_id)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Delete from KùzuDB
    graph_db.delete_document_subgraph(doc_id)

    # 2. Delete file from local storage
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Failed to remove physical file {doc.file_path}: {e}")

    # 3. Cascading delete in SQL
    session.delete(doc)
    session.commit()

    return {"success": True, "deleted_id": doc_id, "message": "Document cascade deleted successfully."}
