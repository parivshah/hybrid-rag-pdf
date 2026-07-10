import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  AskResponse,
  StatusResponse,
  askQuestion,
  fetchStatus,
  resetDocuments,
  uploadDocument,
} from "./api";
import "./App.css";

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [resetOnUpload, setResetOnUpload] = useState(true);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await fetchStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load status");
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  async function handleUpload(file: File) {
    setUploading(true);
    setError(null);
    setUploadMessage(null);
    setAnswer(null);

    try {
      const result = await uploadDocument(file, resetOnUpload);
      setUploadMessage(
        `Indexed ${result.filename}: ${result.chunks_indexed} chunks (BM25: ${result.bm25_documents} docs).`,
      );
      await refreshStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function onFileInput(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      void handleUpload(file);
    }
    event.target.value = "";
  }

  function onDrop(event: React.DragEvent) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      void handleUpload(file);
    }
  }

  async function onAsk(event: FormEvent) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    setAsking(true);
    setError(null);

    try {
      const result = await askQuestion(trimmed);
      setAnswer(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed");
    } finally {
      setAsking(false);
    }
  }

  async function onReset() {
    if (!confirm("Clear all indexed documents?")) {
      return;
    }

    setError(null);
    setAnswer(null);
    setUploadMessage(null);

    try {
      await resetDocuments();
      await refreshStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Talk to your PDF</h1>
        <p>
          Upload a policy or manual, then ask natural-language questions. Answers are grounded in
          retrieved passages using semantic search, BM25 reranking, and Llama 3 via Ollama.
        </p>
        {status && (
          <div className="status-bar">
            <span className="pill">
              Chunks: <strong>{status.chunk_count}</strong>
            </span>
            <span className="pill">
              LLM: <strong className="mono">{status.llm_model}</strong>
            </span>
            <span className="pill">
              Embeddings: <strong className="mono">{status.embed_model}</strong>
            </span>
            <span className="pill">
              Retrieval: <strong>semantic → BM25 → top-{status.top_k}</strong>
            </span>
          </div>
        )}
      </header>

      {error && <div className="message error">{error}</div>}
      {uploadMessage && <div className="message success">{uploadMessage}</div>}

      <div className="grid">
        <section className="card">
          <h2>1. Upload document</h2>
          <p className="hint">PDF or plain text. Text is chunked, embedded with nomic-embed-text, and stored in ChromaDB.</p>

          <div
            className={`upload-zone ${dragging ? "dragging" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <p style={{ margin: "0 0 1rem", color: "var(--text-muted)", fontSize: "0.9rem" }}>
              Drag & drop a file here, or choose one
            </p>
            <label className="upload-label">
              {uploading ? (
                <>
                  <span className="spinner" />
                  Indexing…
                </>
              ) : (
                "Choose PDF"
              )}
              <input type="file" accept=".pdf,.txt" onChange={onFileInput} disabled={uploading} />
            </label>
          </div>

          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={resetOnUpload}
              onChange={(e) => setResetOnUpload(e.target.checked)}
            />
            Replace existing index on upload
          </label>

          <div className="actions">
            <button type="button" className="btn-secondary" onClick={() => void onReset()}>
              Clear index
            </button>
          </div>

          {status && status.sources.length > 0 && (
            <p className="hint" style={{ marginTop: "1rem", marginBottom: 0 }}>
              Indexed: {status.sources.join(", ")}
            </p>
          )}
        </section>

        <section className="card">
          <h2>2. Ask a question</h2>
          <p className="hint">
            Out-of-scope questions are declined when retrieval scores are too low (anti-hallucination).
          </p>

          <form className="question-form" onSubmit={onAsk}>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. What is my deductible for wind damage?"
              disabled={asking || (status?.chunk_count ?? 0) === 0}
            />
            <button
              type="submit"
              className="btn-primary"
              disabled={asking || !question.trim() || (status?.chunk_count ?? 0) === 0}
            >
              {asking ? (
                <>
                  <span className="spinner" />
                  Thinking…
                </>
              ) : (
                "Ask"
              )}
            </button>
          </form>
        </section>

        {answer && (
          <section className="card answer-panel full-width">
            <span className={`badge ${answer.refused ? "refused" : "grounded"}`}>
              {answer.refused ? "Declined / not in document" : "Grounded answer"}
            </span>
            <p className="answer-text">{answer.answer}</p>

            {answer.sources.length > 0 && (
              <div className="sources">
                <h3>Source passages ({answer.use_rerank ? "semantic + BM25" : "semantic only"})</h3>
                {answer.sources.map((source) => (
                  <article key={source.rank} className="source-item">
                    <div className="source-meta">
                      <span>
                        #{source.rank} · {source.source} · chunk {source.chunk_index}
                      </span>
                      {source.semantic_rank != null && <span>semantic rank {source.semantic_rank}</span>}
                      {source.bm25_score != null && <span>BM25 {source.bm25_score}</span>}
                      {source.distance != null && <span>distance {source.distance}</span>}
                    </div>
                    <p className="source-excerpt">{source.excerpt}</p>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
