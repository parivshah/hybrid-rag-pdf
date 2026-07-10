export interface SourceSnippet {
  rank: number;
  source: string;
  chunk_index: number;
  semantic_rank: number | null;
  bm25_score: number | null;
  distance: number | null;
  excerpt: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: SourceSnippet[];
  grounded: boolean;
  refused: boolean;
  use_rerank: boolean;
}

export interface StatusResponse {
  chunk_count: number;
  bm25_documents: number;
  sources: string[];
  embed_model: string;
  llm_model: string;
  retrieval_candidates: number;
  top_k: number;
}

export interface IngestResponse {
  filename: string;
  chunks_indexed: number;
  total_chunks: number;
  bm25_documents: number;
}

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : "Request failed";
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export async function fetchStatus(): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE}/api/status`);
  return handleResponse<StatusResponse>(response);
}

export async function uploadDocument(file: File, reset = false): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/api/documents/upload?reset=${reset}`, {
    method: "POST",
    body: form,
  });
  return handleResponse<IngestResponse>(response);
}

export async function askQuestion(
  question: string,
  options?: { top_k?: number; use_rerank?: boolean },
): Promise<AskResponse> {
  const response = await fetch(`${API_BASE}/api/chat/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      top_k: options?.top_k,
      use_rerank: options?.use_rerank ?? true,
    }),
  });
  return handleResponse<AskResponse>(response);
}

export async function resetDocuments(): Promise<void> {
  const response = await fetch(`${API_BASE}/api/documents`, { method: "DELETE" });
  await handleResponse(response);
}
