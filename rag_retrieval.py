"""Lightweight RAG: BM25 over UTF-8 text/markdown chunks from a directory (no embeddings API)."""

import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from observability import log_event

# Chunking tuned for syllabus-style prose; adjust if needed.
CHUNK_MAX_CHARS = 900
CHUNK_OVERLAP = 120
TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+|[\u0080-\uFFFF]+", (text or "").lower())


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _chunk_text(text: str, source: str) -> list[tuple[str, str]]:
    """Return [(source_label, chunk), ...]."""
    chunks: list[tuple[str, str]] = []
    for para in _split_paragraphs(text):
        if len(para) <= CHUNK_MAX_CHARS:
            chunks.append((source, para))
            continue
        start = 0
        while start < len(para):
            end = min(start + CHUNK_MAX_CHARS, len(para))
            piece = para[start:end].strip()
            if piece:
                chunks.append((source, piece))
            if end >= len(para):
                break
            start = max(0, end - CHUNK_OVERLAP)
    return chunks


def load_corpus_chunks(rag_dir: Path) -> list[tuple[str, str]]:
    """Load (relative_path, chunk) from all text files under rag_dir."""
    if not rag_dir.is_dir():
        raise FileNotFoundError(f"RAG directory not found: {rag_dir.resolve()}")
    pairs: list[tuple[str, str]] = []
    for path in sorted(rag_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        rel = str(path.relative_to(rag_dir))
        text = path.read_text(encoding="utf-8", errors="replace")
        for src, chunk in _chunk_text(text, rel):
            pairs.append((src, chunk))
    return pairs


def retrieve_context(
    query: str,
    pairs: list[tuple[str, str]],
    top_k: int,
) -> list[tuple[str, str, float]]:
    """BM25 retrieve; returns [(source, chunk, score), ...] sorted best-first."""
    if not pairs or top_k <= 0:
        return []
    pairs = [(s, c) for s, c in pairs if _tokenize(c)]
    if not pairs:
        return []
    chunks = [c for _, c in pairs]
    sources = [s for s, _ in pairs]
    tokenized = [_tokenize(c) for c in chunks]
    if not any(tokenized):
        return []
    bm25 = BM25Okapi(tokenized)
    q_tokens = _tokenize(query)
    if not q_tokens:
        q_tokens = ["a"]
    scores = bm25.get_scores(q_tokens)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [(sources[i], chunks[i], float(scores[i])) for i in ranked]


def augment_references_with_rag(
    topic: str,
    base_references: str,
    rag_dir: Path,
    top_k: int = 5,
) -> str:
    """Append BM25-retrieved chunks to the References block for the generator."""
    pairs = load_corpus_chunks(rag_dir)
    if not pairs:
        log_event(
            "rag_skip",
            reason="no_chunks",
            rag_dir=str(rag_dir.resolve()),
        )
        return base_references

    query = f"{topic}\n{base_references}".strip()
    hits = retrieve_context(query, pairs, top_k=top_k)
    log_event(
        "rag_retrieve",
        rag_dir=str(rag_dir.resolve()),
        corpus_chunks=len(pairs),
        top_k=top_k,
        hits=len(hits),
    )
    if not hits:
        return base_references

    lines = [
        "\n\n--- Retrieved context (RAG, BM25) ---",
    ]
    for i, (src, chunk, score) in enumerate(hits, start=1):
        lines.append(f"\n[#{i} source={src} score={score:.4f}]\n{chunk}")
    rag_block = "\n".join(lines)
    if base_references.strip():
        return base_references.rstrip() + rag_block
    return rag_block.lstrip()
