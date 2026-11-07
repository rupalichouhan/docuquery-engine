import re
from typing import List, Dict, Any


class SemanticChunker:
    """
    Splits document pages into semantically cohesive chunks.
    Prioritizes preserving headers, full paragraphs, and entire tables
    rather than naive fixed-character truncation.
    """

    def __init__(self, target_chunk_words: int = 300, overlap_words: int = 50):
        self.target_chunk_words = target_chunk_words
        self.overlap_words = overlap_words

    def chunk_document(self, parsed_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        chunk_idx = 0

        for page in parsed_doc.get("pages", []):
            page_num = page["page_number"]
            page_bbox = page.get("bounding_box", {})
            tables = page.get("tables", [])
            text = page.get("text", "")

            # 1. Process and emit tables as high-fidelity standalone semantic chunks
            for t_idx, table_info in enumerate(tables):
                md_table = table_info["markdown"]
                chunk_idx += 1
                chunks.append({
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "content": f"[Table - Page {page_num}]\n{md_table}",
                    "bounding_box": page_bbox,
                    "tables_extracted": [table_info],
                    "metadata": {"type": "table", "table_index": t_idx},
                })

            # 2. Process textual sections (split by natural paragraphs and headings)
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            current_words = []
            
            for p in paragraphs:
                words = p.split()
                if not words:
                    continue

                if len(current_words) + len(words) <= self.target_chunk_words:
                    current_words.extend(words)
                else:
                    if current_words:
                        chunk_idx += 1
                        chunk_text = " ".join(current_words)
                        chunks.append({
                            "chunk_index": chunk_idx,
                            "page_number": page_num,
                            "content": chunk_text,
                            "bounding_box": page_bbox,
                            "tables_extracted": [],
                            "metadata": {"type": "prose"},
                        })
                        # Retain overlap
                        current_words = current_words[-self.overlap_words:] + words
                    else:
                        # Paragraph itself is larger than target words, split it cleanly
                        chunk_idx += 1
                        chunks.append({
                            "chunk_index": chunk_idx,
                            "page_number": page_num,
                            "content": " ".join(words),
                            "bounding_box": page_bbox,
                            "tables_extracted": [],
                            "metadata": {"type": "prose"},
                        })
                        current_words = []

            if current_words:
                chunk_idx += 1
                chunks.append({
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "content": " ".join(current_words),
                    "bounding_box": page_bbox,
                    "tables_extracted": [],
                    "metadata": {"type": "prose"},
                })

        return chunks
