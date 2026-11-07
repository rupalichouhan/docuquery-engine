import { DocumentItem, ChatMessage, GraphData } from '@/types';

const rawBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
// Strip any accidental trailing slashes or /api/v1 prefix to ensure clean routing
const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '').replace(/\/api\/v1\/?$/, '');

export async function fetchDocuments(): Promise<DocumentItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/documents`, { cache: 'no-store' });
    if (!res.ok) throw new Error('Failed to fetch documents');
    return await res.json();
  } catch (err) {
    console.error('fetchDocuments error:', err);
    return [];
  }
}

export async function uploadDocument(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Document upload failed');
  }

  return await res.json();
}

export async function deleteDocument(docId: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
  return await res.json();
}

export async function executeQuery(
  query: string,
  documentIds?: string[],
  verifyMath: boolean = true
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      document_ids: documentIds && documentIds.length > 0 ? documentIds : null,
      verify_math: verifyMath,
      top_k: 5,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Query execution failed');
  }

  return await res.json();
}

export async function runEvaluation(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/evaluation/run`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Evaluation failed');
  return await res.json();
}

export async function exploreGraph(entity: string): Promise<GraphData> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/graph/explore?entity=${encodeURIComponent(entity)}`
  );
  if (!res.ok) throw new Error('Graph exploration failed');
  return await res.json();
}

export function getDocumentPdfUrl(docId: string): string {
  return `${API_BASE_URL}/api/v1/documents/${docId}/file`;
}
