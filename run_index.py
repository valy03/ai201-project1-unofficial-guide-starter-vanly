"""Build the vector store (Milestone 4).

Run from the repo root after collecting documents:

    python run_index.py

Loads documents/ -> chunks -> embeds with all-MiniLM-L6-v2 -> stores in
ChromaDB. Re-run any time you change documents or chunking; it rebuilds
the collection from scratch. The first run downloads the model (~90MB).
"""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from vector_store import build_index  # noqa: E402

if __name__ == "__main__":
    count = build_index()
    print(f"\nDone. {count} chunks indexed and ready to query.")
