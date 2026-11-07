import os
import uuid
import shutil
from app.db.session import SessionLocal, init_db
from app.db.models import Document
from app.ingestion.pipeline import pipeline
from app.core.config import settings

def seed_document():
    init_db()
    source_pdf = "./data/sample_documents/DocuQuery_Technical_Financial_Report.pdf"
    if not os.path.exists(source_pdf):
        raise FileNotFoundError(f"Missing {source_pdf}")

    doc_id = str(uuid.uuid4())
    filename = "DocuQuery_Technical_Financial_Report.pdf"
    dest_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    shutil.copy(source_pdf, dest_path)

    file_size = os.path.getsize(dest_path)

    with SessionLocal() as session:
        # Check if already seeded
        existing = session.query(Document).filter(Document.filename == filename).first()
        if existing:
            print(f"Document already exists in DB: {existing.id}")
            return existing.id

        new_doc = Document(
            id=doc_id,
            title="DocuQuery Technical & Financial Report 2024",
            filename=filename,
            file_path=dest_path,
            file_size_bytes=file_size,
            mime_type="application/pdf",
            status="PENDING",
        )
        session.add(new_doc)
        session.commit()

        print(f"Starting ingestion for seeded document: {doc_id}")
        res = pipeline.process_document(doc_id, dest_path, session)
        print(f"Ingestion result: {res}")
        return doc_id

if __name__ == "__main__":
    seed_document()
