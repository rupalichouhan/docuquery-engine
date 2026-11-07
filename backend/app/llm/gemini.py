import re
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class LLMProvider:
    """Base interface for LLM synthesis."""

    def generate_grounded_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        raise NotImplementedError


class GeminiLLMProvider(LLMProvider):
    """Google Gemini 2.5 Flash implementation using the official google-genai SDK."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.client = None
        if self.api_key and len(self.api_key.strip()) > 5:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize google-genai client: {e}")

    def generate_grounded_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesizes an answer grounded strictly in retrieved context chunks.
        Inserts citation markers [Doc: <Title>, Page: <Page>].
        Abstains if context is insufficient.
        """
        if not context_chunks:
            return {
                "answer": "I cannot answer this based on the provided documents. No relevant context was found.",
                "citations": [],
            }

        # Build numbered context block
        context_lines = []
        citations_available = []
        for idx, c in enumerate(context_chunks, start=1):
            doc_title = c.get("doc_title", "Document")
            page_num = c.get("page_number", 1)
            content = c.get("content", "").strip()
            citation_tag = f"[Doc: {doc_title}, Page: {page_num}]"
            context_lines.append(f"Context [{idx}] {citation_tag}:\n{content}\n")
            citations_available.append({
                "tag": citation_tag,
                "doc_id": c.get("document_id"),
                "doc_title": doc_title,
                "page_number": page_num,
                "bounding_box": c.get("bounding_box"),
                "content_snippet": content[:250],
            })

        formatted_context = "\n---\n".join(context_lines)

        system_instruction = (
            "You are DocuQuery Engine, an elite document intelligence research assistant. "
            "Your answers must be strictly grounded in the provided contexts. "
            "Follow these critical rules:\n"
            "1. Every factual claim must be followed immediately by its citation tag, e.g. [Doc: Name, Page: X].\n"
            "2. Distinguish clearly between direct facts stated in the documents and reasonable synthesis.\n"
            "3. If the provided context does not contain enough evidence to answer the question, you MUST say: "
            "'I cannot answer this based on the provided documents.' Do not extrapolate or hallucinate.\n"
            "4. When reporting numerical figures, preserve exact numbers, units, and currencies from the text/tables."
        )

        user_prompt = f"""Question: {query}

Provided Context:
{formatted_context}

Please provide a structured, comprehensive, and cited answer:"""

        candidate_models = [
            self.model_name,
            "gemini-3.8-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        # Remove duplicates while preserving order
        candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

        if self.client:
            for model_to_try in candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_to_try,
                        contents=user_prompt,
                        config={"system_instruction": system_instruction, "temperature": 0.1},
                    )
                    answer_text = response.text.strip()
                    # Parse cited tags in the answer
                    used_citations = []
                    for cit in citations_available:
                        if cit["tag"] in answer_text or f"Page: {cit['page_number']}" in answer_text:
                            used_citations.append(cit)

                    return {
                        "answer": answer_text,
                        "citations": used_citations or citations_available[:3],
                    }
                except Exception as e:
                    logger.warning(f"Gemini API model '{model_to_try}' attempt notice: {e}")

        # Structured Extractive Fallback synthesis (Offline / Network Unreachable)
        key_points = []
        for c in context_chunks[:3]:
            doc_title = c.get("doc_title", "Document")
            page_num = c.get("page_number", 1)
            raw = c.get("content", "").strip()
            # Cleanly grab primary declarative sentences
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if len(s.strip()) > 25]
            if sentences:
                snippet = " ".join(sentences[:2])
                key_points.append(f"• {snippet} [Doc: {doc_title}, Page: {page_num}]")

        fallback_answer = (
            "### Grounded Research Findings\n\n"
            + "\n\n".join(key_points)
            if key_points
            else f"Relevant document evidence:\n\n{context_chunks[0].get('content')[:400]}"
        )
        return {
            "answer": fallback_answer,
            "citations": citations_available[:3],
        }


llm_provider = GeminiLLMProvider()
