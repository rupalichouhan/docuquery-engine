export interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  file_size_bytes: number;
  total_pages: number;
  status: 'PENDING' | 'PARSING' | 'CHUNKING' | 'EXTRACTING' | 'INDEXING' | 'COMPLETED' | 'FAILED';
  current_step?: string;
  error_message?: string | null;
  created_at: string;
}

export interface BoundingBox {
  x0: number;
  top: number;
  x1: number;
  bottom: number;
  width: number;
  height: number;
}

export interface Citation {
  tag: string;
  doc_id?: string;
  doc_title: string;
  page_number: number;
  bounding_box?: BoundingBox | null;
  content_snippet?: string;
}

export interface VerificationBadge {
  claim: string;
  formula: string;
  claimed_value: number;
  calculated_value: number | null;
  is_verified: boolean;
  badge: string;
  badge_variant: 'success' | 'warning' | 'destructive';
  evidence?: string | null;
  details?: string;
  error?: string | null;
}

export interface RAGMetrics {
  total_latency_ms: number;
  rerank_latency_ms: number;
  vector_candidates: number;
  graph_candidates: number;
  context_chunks_used: number;
  verification_count: number;
  graph_nodes_count: number;
  graph_edges_count: number;
}

export interface GraphNode {
  id: string;
  label: string;
  category: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  evidence?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ContextChunk {
  chunk_id: string;
  doc_title: string;
  page_number: number;
  rerank_score: number;
  content: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  verification?: VerificationBadge[];
  metrics?: RAGMetrics;
  graph_subgraph?: GraphData;
  context_chunks?: ContextChunk[];
  timestamp: string;
}
