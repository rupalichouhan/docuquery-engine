import re
import time
from collections import defaultdict
from fastapi import HTTPException, Request, UploadFile, status
from app.core.config import settings

# PDF header signature: %PDF-
PDF_MAGIC_BYTES = b"%PDF-"

def sanitize_filename(filename: str) -> str:
    """Strip path traversal characters and normalize file name."""
    clean = re.sub(r"[^\w\s\.-]", "_", filename)
    clean = clean.strip("._ ")
    return clean or "unnamed_document.pdf"

async def validate_pdf_upload(file: UploadFile) -> bytes:
    """Validate PDF file size, mime type, and magic bytes."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported.",
        )

    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # Conforming PDF specification allows header anywhere in first 1024 bytes (handles BOM, whitespace, comments)
    if PDF_MAGIC_BYTES not in content[:1024]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match a valid PDF signature.",
        )

    return content


class InMemoryRateLimiter:
    """Lightweight in-memory rate limiter per IP address."""
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def check(self, request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - self.window_seconds
        
        # Keep only recent requests
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip] if ts > window_start
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down your requests.",
            )
        self.requests[client_ip].append(now)

rate_limiter = InMemoryRateLimiter(max_requests=100, window_seconds=60)
