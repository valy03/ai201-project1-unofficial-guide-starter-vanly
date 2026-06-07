"""Test retrieval against the evaluation questions (Milestone 4).

Run from the repo root (after `python run_index.py`):

    python run_retrieval.py

Runs each evaluation-plan query through retrieve() and prints the top-k
chunks with their source and cosine distance, so you can judge whether
retrieval is returning on-topic content from the right source. Good top
results sit well below 0.5.
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from vector_store import retrieve  # noqa: E402

# The 5 evaluation questions from planning.md.
EVAL_QUERIES = [
    "What are the operating hours of the College Nine / John R. Lewis dining hall?",
    "Can I use Banana Bucks at any dining hall, and do they roll over between quarters?",
    "Which dining hall do UCSC students consider the best, and why?",
    "What off-campus restaurants near UCSC do students recommend?",
    "How much have dining hall prices risen for the 2026-2027 year?",
]

K = 5
PREVIEW_CHARS = 280


def main() -> None:
    for i, query in enumerate(EVAL_QUERIES, 1):
        print("=" * 78)
        print(f"Q{i}: {query}")
        print("=" * 78)
        for rank, r in enumerate(retrieve(query, k=K), 1):
            flag = "  <-- weak (>0.5)" if r.distance > 0.5 else ""
            preview = r.text[:PREVIEW_CHARS].replace("\n", " ")
            if len(r.text) > PREVIEW_CHARS:
                preview += "..."
            print(f"\n  [{rank}] distance={r.distance:.3f}{flag}  source: {r.source}")
            print(f"      {preview}")
        print()


if __name__ == "__main__":
    main()
