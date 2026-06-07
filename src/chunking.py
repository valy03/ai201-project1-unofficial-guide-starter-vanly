"""Recursive, token-based chunking for The Unofficial Guide (Milestone 3).

Implements the Chunking Strategy from planning.md:
    - chunk size : 256 tokens   (matches the all-MiniLM-L6-v2 input limit)
    - overlap    : 35 tokens    (~15% of chunk size)
    - recursive  : split on natural separators (paragraph -> line -> sentence
                   -> word) before any hard cut, so facts are not severed
                   mid-sentence and short reviews pass through whole.

Length is measured in *tokens* using the all-MiniLM-L6-v2 tokenizer (the same
model used for embeddings) so a chunk never overflows the encoder's 256-token
window. If the tokenizer can't be loaded, we fall back to a ~4-chars-per-token
estimate and warn.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Defaults come straight from planning.md.
CHUNK_SIZE = 256      # tokens
OVERLAP = 35          # tokens
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Separators tried in priority order: paragraph, line, sentence, clause, word.
_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

_tokenizer = None
_tokenizer_loaded = False


def _get_tokenizer():
    """Lazily load the MiniLM tokenizer; cache the result (or None on failure)."""
    global _tokenizer, _tokenizer_loaded
    if _tokenizer_loaded:
        return _tokenizer
    _tokenizer_loaded = True
    try:
        from transformers import AutoTokenizer
        from transformers import logging as hf_logging
        hf_logging.set_verbosity_error()  # silence the >512-token length notice
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    except Exception as exc:  # noqa: BLE001 - any failure -> heuristic fallback
        print(f"  ! tokenizer unavailable ({exc}); using ~4-chars/token estimate")
        _tokenizer = None
    return _tokenizer


def token_len(text: str) -> int:
    """Number of tokens in ``text`` (no special tokens), or an estimate."""
    tok = _get_tokenizer()
    if tok is None:
        return max(1, round(len(text) / 4))
    return len(tok.encode(text, add_special_tokens=False))


@dataclass
class Chunk:
    """A retrievable piece of text with the metadata needed for attribution."""

    text: str
    source: str
    url: str
    chunk_index: int          # position of this chunk within its document
    token_count: int
    metadata: dict = field(default_factory=dict)


def _recursive_segments(text: str, max_tokens: int, separators: list[str]) -> list[str]:
    """Break ``text`` into segments that each fit within ``max_tokens``.

    Tries separators in priority order; only falls back to a hard token slice
    when no separator remains (i.e. a single very long word/URL).
    """
    text = text.strip()
    if not text:
        return []
    if token_len(text) <= max_tokens:
        return [text]

    # Find the first separator that actually occurs in the text.
    sep, rest = "", separators[-1:]
    for i, candidate in enumerate(separators):
        if candidate == "":
            sep, rest = "", []
            break
        if candidate in text:
            sep, rest = candidate, separators[i + 1:]
            break

    if sep == "":
        return _hard_split_by_tokens(text, max_tokens)

    segments: list[str] = []
    for part in text.split(sep):
        part = part.strip()
        if not part:
            continue
        if token_len(part) <= max_tokens:
            segments.append(part)
        else:
            segments.extend(_recursive_segments(part, max_tokens, rest))
    return segments


def _hard_split_by_tokens(text: str, max_tokens: int) -> list[str]:
    """Last resort: slice token ids into windows when nothing else splits."""
    tok = _get_tokenizer()
    if tok is None:
        # Estimate-based character windows (~4 chars/token).
        width = max_tokens * 4
        return [text[i:i + width].strip() for i in range(0, len(text), width)]
    ids = tok.encode(text, add_special_tokens=False)
    pieces = []
    for i in range(0, len(ids), max_tokens):
        pieces.append(tok.decode(ids[i:i + max_tokens]).strip())
    return [p for p in pieces if p]


def _merge_segments(segments: list[str], max_tokens: int, overlap: int) -> list[str]:
    """Greedily pack segments into chunks, carrying an overlap tail forward.

    Length is measured on the *joined* text rather than summed per segment,
    because re-tokenizing a joined string is not the same as adding the token
    counts of its parts (so a sum can undershoot and overflow the limit).
    """
    chunks: list[str] = []
    current: list[str] = []

    for seg in segments:
        if current and token_len(" ".join(current + [seg])) > max_tokens:
            chunks.append(" ".join(current))
            # Build the overlap tail from the end of the chunk we just emitted,
            # but only keep tail segments that still leave room for `seg` within
            # the limit (overlap is best-effort; never overflow the chunk).
            tail: list[str] = []
            for prev in reversed(current):
                if token_len(" ".join([prev] + tail)) > overlap:
                    break
                if token_len(" ".join([prev] + tail + [seg])) > max_tokens:
                    break
                tail.insert(0, prev)
            current = tail
        current.append(seg)

    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_text(
    text: str,
    source: str = "",
    url: str = "",
    chunk_size: int = CHUNK_SIZE,
    overlap: int = OVERLAP,
) -> list[Chunk]:
    """Split one document's text into overlapping, token-bounded chunks."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    segments = _recursive_segments(text, chunk_size, _SEPARATORS)
    pieces = _merge_segments(segments, chunk_size, overlap)

    return [
        Chunk(
            text=piece,
            source=source,
            url=url,
            chunk_index=i,
            token_count=token_len(piece),
            metadata={"source": source, "url": url, "chunk_index": i},
        )
        for i, piece in enumerate(pieces)
    ]


def chunk_documents(documents, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP):
    """Chunk a list of ingest.Document objects into a flat list of Chunks."""
    all_chunks: list[Chunk] = []
    for doc in documents:
        all_chunks.extend(
            chunk_text(doc.text, doc.source, doc.url, chunk_size, overlap)
        )
    return all_chunks
