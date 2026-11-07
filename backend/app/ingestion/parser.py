from typing import List, Dict, Any
import pdfplumber
from pypdf import PdfReader
from app.core.logging import logger


class PDFDocumentParser:
    """Extracts text, bounding boxes, and tabular structures from PDF documents."""

    @staticmethod
    def parse(file_path: str) -> Dict[str, Any]:
        """
        Parses a PDF file and returns pages with clean text, bounding boxes,
        and extracted markdown tables.
        """
        pages_data = []
        total_pages = 0

        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                for page_idx, page in enumerate(pdf.pages, start=1):
                    # 1. Extract raw words with positions for bounding boxes
                    words = page.extract_words() or []
                    
                    # 2. Extract tables and convert to clean markdown format
                    extracted_tables = []
                    tables = page.extract_tables() or []
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        # Clean cells
                        cleaned_rows = []
                        for row in table:
                            cleaned_row = [
                                str(cell).replace("\n", " ").strip() if cell is not None else ""
                                for cell in row
                            ]
                            if any(cleaned_row):
                                cleaned_rows.append(cleaned_row)

                        if len(cleaned_rows) >= 2:
                            headers = cleaned_rows[0]
                            header_line = "| " + " | ".join(headers) + " |"
                            sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
                            body_lines = [
                                "| " + " | ".join(r[:len(headers)]) + " |"
                                for r in cleaned_rows[1:]
                            ]
                            md_table = "\n".join([header_line, sep_line] + body_lines)
                            extracted_tables.append({
                                "markdown": md_table,
                                "raw_rows": cleaned_rows,
                            })

                    # 3. Extract text
                    page_text = page.extract_text(layout=True) or ""
                    
                    # Compute page-level bounding box bounds
                    page_bbox = {
                        "x0": min((w["x0"] for w in words), default=0.0),
                        "top": min((w["top"] for w in words), default=0.0),
                        "x1": max((w["x1"] for w in words), default=float(page.width)),
                        "bottom": max((w["bottom"] for w in words), default=float(page.height)),
                        "width": float(page.width),
                        "height": float(page.height),
                    }

                    pages_data.append({
                        "page_number": page_idx,
                        "text": page_text,
                        "tables": extracted_tables,
                        "bounding_box": page_bbox,
                    })

        except Exception as e:
            logger.error(f"pdfplumber parse error on {file_path}, falling back to pypdf: {e}")
            # Fallback to standard pypdf
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            for page_idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages_data.append({
                    "page_number": page_idx,
                    "text": text,
                    "tables": [],
                    "bounding_box": {"x0": 0, "top": 0, "x1": 612, "bottom": 792, "width": 612, "height": 792},
                })

        return {
            "total_pages": total_pages,
            "pages": pages_data,
        }
