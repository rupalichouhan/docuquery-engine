import re
import json
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.core.logging import logger

# Base entity patterns
COMPANY_PATTERN = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*(?:\s+(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|Technologies|Group|Holdings|Co\.?))\b)")
METRIC_PATTERN = re.compile(r"\b(Revenue|EBITDA|Net\s+Income|Operating\s+Margin|Gross\s+Margin|CapEx|Free\s+Cash\s+Flow|Operating\s+Income|ARR|Diluted\s+EPS|Earnings\s+Per\s+Share)\b", re.IGNORECASE)
CURRENCY_PATTERN = re.compile(r"(?:\$|€|£|₹|Rs\.?)\s?\d+(?:,\d{3})*(?:\.\d+)?(?:\s?(?:million|billion|trillion|M|B|K|Crore))?", re.IGNORECASE)
PERCENTAGE_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?%")
QUARTER_YEAR_PATTERN = re.compile(r"\b(?:Q[1-4]\s*(?:20\d\d)?|FY\s*20\d\d|20\d\d)\b")


class HybridEntityExtractor:
    """Extracts entities and relational edges using local NLP + Gemini."""

    def extract_local_entities(self, text: str) -> List[Dict[str, str]]:
        """Fast local pattern-based entity extraction."""
        entities = {}

        # 1. Companies
        for match in COMPANY_PATTERN.finditer(text):
            val = match.group(0).strip()
            entities[val] = "COMPANY"

        # 2. Financial Metrics
        for match in METRIC_PATTERN.finditer(text):
            val = match.group(0).strip().title()
            entities[val] = "METRIC"

        # 3. Currency Amounts
        for match in CURRENCY_PATTERN.finditer(text):
            val = match.group(0).strip()
            entities[val] = "CURRENCY"

        # 4. Percentages
        for match in PERCENTAGE_PATTERN.finditer(text):
            val = match.group(0).strip()
            entities[val] = "PERCENTAGE"

        # 5. Quarter / Year
        for match in QUARTER_YEAR_PATTERN.finditer(text):
            val = match.group(0).strip()
            entities[val] = "TIMEFRAME"

        return [{"name": name, "category": cat} for name, cat in entities.items()]

    async def extract_relations(
        self,
        text: str,
        entities: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """
        Extract directed relationships between entities.
        Uses Gemini if configured, otherwise falls back to local co-occurrence rules.
        """
        if not entities or len(entities) < 2:
            return []

        # If Gemini API Key is available, prompt Gemini for high-level semantic edges
        if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = f"""Given the following text and known entities, extract up to 5 key relationships as JSON.
Known Entities: {[e['name'] for e in entities[:10]]}
Text:
\"\"\"{text[:1500]}\"\"\"

Return ONLY a JSON array of objects with keys: "source", "target", "relation_type", "evidence".
Example: [{{"source": "Apple", "target": "Revenue", "relation_type": "REPORTED_VALUE", "evidence": "Revenue was $85B"}}]
"""
                response = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )
                raw = response.text.strip()
                # Clean json fences if present
                if raw.startswith("```"):
                    raw = re.sub(r"^```(?:json)?\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw)
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
            except Exception as e:
                logger.warning(f"Gemini relation extraction fallback: {e}")

        # Local rule-based fallback: Co-occurrence within sentences
        return self._local_relation_heuristics(text, entities)

    def _local_relation_heuristics(
        self,
        text: str,
        entities: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """Deterministic relationship linking based on entity proximity."""
        relations = []
        sentences = [s.strip() for s in re.split(r"[.!?\n]", text) if s.strip()]
        
        ent_names = [e["name"] for e in entities]
        ent_lookup = {e["name"]: e["category"] for e in entities}

        for s in sentences:
            present = [name for name in ent_names if name.lower() in s.lower()]
            if len(present) >= 2:
                # Link pairs in sentence
                for i in range(len(present) - 1):
                    src = present[i]
                    tgt = present[i + 1]
                    src_cat = ent_lookup.get(src, "CONCEPT")
                    tgt_cat = ent_lookup.get(tgt, "CONCEPT")

                    rel_type = "RELATED_TO"
                    if src_cat == "COMPANY" and tgt_cat == "METRIC":
                        rel_type = "MEASURES"
                    elif src_cat == "METRIC" and tgt_cat in ("CURRENCY", "PERCENTAGE"):
                        rel_type = "VALUED_AT"
                    elif tgt_cat == "TIMEFRAME":
                        rel_type = "REPORTED_IN"

                    relations.append({
                        "source": src,
                        "target": tgt,
                        "relation_type": rel_type,
                        "evidence": s[:200],
                    })
                    if len(relations) >= 8:
                        break
        return relations


extractor = HybridEntityExtractor()
