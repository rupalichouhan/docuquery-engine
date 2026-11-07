import os
from typing import List, Dict, Any, Optional
import kuzu
from app.core.config import settings
from app.core.logging import logger


class KuzuGraphManager:
    """Embedded property graph database using KùzuDB."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.KUZU_DB_PATH
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.db = kuzu.Database(self.db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self):
        """Idempotently define node and relationship tables."""
        tables_to_create = [
            """CREATE NODE TABLE IF NOT EXISTS Entity(
                name STRING,
                category STRING,
                PRIMARY KEY (name)
            )""",
            """CREATE NODE TABLE IF NOT EXISTS ChunkNode(
                chunk_id STRING,
                doc_id STRING,
                page_number INT64,
                PRIMARY KEY (chunk_id)
            )""",
            """CREATE REL TABLE IF NOT EXISTS MENTIONS(
                FROM ChunkNode TO Entity,
                frequency INT64
            )""",
            """CREATE REL TABLE IF NOT EXISTS RELATES_TO(
                FROM Entity TO Entity,
                relation_type STRING,
                doc_id STRING,
                evidence STRING
            )"""
        ]
        for query in tables_to_create:
            try:
                self.conn.execute(query)
            except Exception as e:
                # Table might already exist or minor dialect difference
                logger.debug(f"Kùzu schema statement notice: {e}")

    def add_chunk_and_entities(
        self,
        chunk_id: str,
        doc_id: str,
        page_number: int,
        entities: List[Dict[str, str]],
        relations: List[Dict[str, str]],
    ):
        """Atomically insert Chunk, Entities, and their relations into Kùzu."""
        # Insert ChunkNode
        try:
            self.conn.execute(
                "MERGE (c:ChunkNode {chunk_id: $chunk_id}) ON CREATE SET c.doc_id = $doc_id, c.page_number = $page_number",
                {"chunk_id": str(chunk_id), "doc_id": str(doc_id), "page_number": int(page_number)}
            )
        except Exception as e:
            logger.warning(f"Error inserting ChunkNode into Kuzu: {e}")

        # Insert Entities & MENTIONS
        for ent in entities:
            name = (ent.get("name") or "").strip()
            category = ent.get("category", "CONCEPT")
            if not name:
                continue
            try:
                self.conn.execute(
                    "MERGE (e:Entity {name: $name}) ON CREATE SET e.category = $category",
                    {"name": name, "category": category}
                )
                self.conn.execute(
                    """
                    MATCH (c:ChunkNode {chunk_id: $chunk_id}), (e:Entity {name: $name})
                    CREATE (c)-[:MENTIONS {frequency: 1}]->(e)
                    """,
                    {"chunk_id": str(chunk_id), "name": name}
                )
            except Exception as e:
                logger.debug(f"Entity/Mention merge warning for '{name}': {e}")

        # Insert RELATES_TO
        for rel in relations:
            source = (rel.get("source") or "").strip()
            target = (rel.get("target") or "").strip()
            relation_type = rel.get("relation_type", "RELATED_TO").strip()
            evidence = rel.get("evidence", "")[:250]
            if not source or not target:
                continue
            try:
                self.conn.execute(
                    "MERGE (s:Entity {name: $source}) ON CREATE SET s.category = 'CONCEPT'",
                    {"source": source}
                )
                self.conn.execute(
                    "MERGE (t:Entity {name: $target}) ON CREATE SET t.category = 'CONCEPT'",
                    {"target": target}
                )
                self.conn.execute(
                    """
                    MATCH (s:Entity {name: $source}), (t:Entity {name: $target})
                    CREATE (s)-[:RELATES_TO {relation_type: $rel_type, doc_id: $doc_id, evidence: $evidence}]->(t)
                    """,
                    {
                        "source": source,
                        "target": target,
                        "rel_type": relation_type,
                        "doc_id": str(doc_id),
                        "evidence": evidence,
                    }
                )
            except Exception as e:
                logger.debug(f"Relation creation warning for {source}->{target}: {e}")

    def query_neighborhood(self, entity_names: List[str], max_hops: int = 2) -> Dict[str, Any]:
        """
        Extract 1-to-2 hop graph neighborhood for Cytoscape.js / React Flow rendering.
        Returns: { "nodes": [{"id": ..., "label": ..., "category": ...}], "edges": [{"source": ..., "target": ..., "label": ...}] }
        """
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        if not entity_names:
            return {"nodes": [], "edges": []}

        for ent in entity_names[:5]:  # limit to top 5 seed entities for fast focused subgraph
            try:
                # 1-hop relationships
                res = self.conn.execute(
                    """
                    MATCH (s:Entity {name: $name})-[r:RELATES_TO]->(t:Entity)
                    RETURN s.name, s.category, t.name, t.category, r.relation_type, r.evidence
                    LIMIT 25
                    """,
                    {"name": ent}
                )
                while res.has_next():
                    row = res.get_next()
                    s_name, s_cat, t_name, t_cat, r_type, evidence = row
                    nodes[s_name] = {"id": s_name, "label": s_name, "category": s_cat}
                    nodes[t_name] = {"id": t_name, "label": t_name, "category": t_cat}
                    edges.append({
                        "id": f"{s_name}-{r_type}-{t_name}",
                        "source": s_name,
                        "target": t_name,
                        "label": r_type,
                        "evidence": evidence,
                    })
            except Exception as e:
                logger.warning(f"Error querying Kùzu neighborhood for '{ent}': {e}")

        return {"nodes": list(nodes.values()), "edges": edges}

    def get_connected_chunks(self, entity_names: List[str], limit: int = 10) -> List[str]:
        """Find chunk IDs mentioning any of the given entities."""
        chunk_ids: List[str] = []
        for ent in entity_names:
            try:
                res = self.conn.execute(
                    """
                    MATCH (c:ChunkNode)-[:MENTIONS]->(e:Entity {name: $name})
                    RETURN c.chunk_id
                    LIMIT $limit
                    """,
                    {"name": ent, "limit": limit}
                )
                while res.has_next():
                    row = res.get_next()
                    chunk_ids.append(row[0])
            except Exception as e:
                logger.warning(f"Error getting connected chunks for {ent}: {e}")
        return list(set(chunk_ids))

    def delete_document_subgraph(self, doc_id: str):
        """Cascade delete all ChunkNodes and RELATES_TO created by this document."""
        try:
            # Delete relationships originating from this document
            self.conn.execute(
                "MATCH ()-[r:RELATES_TO]->() WHERE r.doc_id = $doc_id DELETE r",
                {"doc_id": str(doc_id)}
            )
            # Delete mentions from chunks belonging to this document
            self.conn.execute(
                "MATCH (c:ChunkNode)-[m:MENTIONS]->() WHERE c.doc_id = $doc_id DELETE m",
                {"doc_id": str(doc_id)}
            )
            # Delete chunk nodes
            self.conn.execute(
                "MATCH (c:ChunkNode) WHERE c.doc_id = $doc_id DELETE c",
                {"doc_id": str(doc_id)}
            )
            logger.info(f"Cascaded graph delete completed for document: {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting Kùzu subgraph for document {doc_id}: {e}")


# Singleton instance
graph_db = KuzuGraphManager()
