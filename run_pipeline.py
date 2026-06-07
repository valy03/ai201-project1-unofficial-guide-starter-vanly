"""Milestone 3 driver: load -> clean -> chunk -> inspect.

Run from the repo root:

    python run_pipeline.py

Prints per-document stats, the total chunk count (with the 50 / 2000 sanity
warnings from the milestone), token-size diagnostics, and 5 representative
chunks spread across the corpus so you can eyeball whether each chunk is a
complete, standalone thought.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Windows consoles default to cp1252 and crash on characters like "⁄"; force UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from chunking import CHUNK_SIZE, OVERLAP, chunk_text  # noqa: E402
from ingest import DOCUMENTS_DIR, load_documents  # noqa: E402


def _representative_indices(n: int, k: int = 5) -> list[int]:
    """Pick up to k indices evenly spread across a list of length n."""
    if n <= k:
        return list(range(n))
    step = n / k
    return [int(i * step) for i in range(k)]


def main() -> None:
    documents_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DOCUMENTS_DIR

    print("=" * 70)
    print("MILESTONE 3 - INGESTION & CHUNKING")
    print(f"chunk_size = {CHUNK_SIZE} tokens   overlap = {OVERLAP} tokens")
    print(f"documents:  {documents_dir}")
    print("=" * 70)

    documents = load_documents(documents_dir)
    if not documents:
        print(
            "\nNo documents found in documents/.\n"
            "Add .txt files (one per source) with a 2-line header:\n\n"
            "    SOURCE: Reddit r/UCSC -- best dining hall thread\n"
            "    URL: https://www.reddit.com/...\n"
            "    ---\n"
            "    <pasted text>\n"
        )
        return

    # ---- Per-document breakdown -------------------------------------------
    print(f"\nLoaded {len(documents)} document(s):\n")
    print(f"{'#':>2}  {'source':<45} {'chars':>7} {'chunks':>7}")
    print("-" * 66)
    total_chunks = 0
    per_doc_chunks = []
    for i, doc in enumerate(documents, 1):
        chunks = chunk_text(doc.text, doc.source, doc.url)
        per_doc_chunks.append((doc, chunks))
        total_chunks += len(chunks)
        label = (doc.source[:42] + "...") if len(doc.source) > 45 else doc.source
        print(f"{i:>2}  {label:<45} {doc.char_len:>7} {len(chunks):>7}")

    all_chunks = [c for _, chunks in per_doc_chunks for c in chunks]

    # ---- Totals + sanity warnings -----------------------------------------
    print("-" * 66)
    print(f"\nTOTAL CHUNKS: {total_chunks}")
    if total_chunks < 50:
        print("  !! Fewer than 50 chunks - chunks may be too large for precise retrieval.")
    elif total_chunks > 2000:
        print("  !! More than 2000 chunks - chunks may be too small to carry meaning.")
    else:
        print("  OK chunk count is in the healthy 50-2000 range.")

    # ---- Token-size diagnostics -------------------------------------------
    token_counts = [c.token_count for c in all_chunks]
    over_limit = sum(1 for t in token_counts if t > CHUNK_SIZE)
    print(
        f"\nToken sizes  min={min(token_counts)}  "
        f"max={max(token_counts)}  "
        f"avg={sum(token_counts) / len(token_counts):.0f}"
    )
    if over_limit:
        print(f"  !! {over_limit} chunk(s) exceed {CHUNK_SIZE} tokens (would be truncated).")
    else:
        print(f"  OK every chunk fits within the {CHUNK_SIZE}-token encoder limit.")

    # ---- 5 representative chunks ------------------------------------------
    print("\n" + "=" * 70)
    print("5 REPRESENTATIVE CHUNKS (read each: is it a complete, standalone thought?)")
    print("=" * 70)
    for idx in _representative_indices(len(all_chunks), 5):
        c = all_chunks[idx]
        print(f"\n--- chunk #{idx}  |  {c.token_count} tokens  |  {c.source} ---")
        print(c.text)
        if c.url:
            print(f"[source: {c.url}]")


if __name__ == "__main__":
    main()
