"""Embedding + vector store for The Unofficial Guide (Milestone 4).

Pipeline stage 3-4 from planning.md:
    - embed every chunk with all-MiniLM-L6-v2 (sentence-transformers)
    - store vectors + source metadata in ChromaDB (cosine distance)
    - retrieve(query, k=5) -> the k closest chunks with their source + distance

Embeddings are L2-normalized and the collection uses cosine space, so the
distance returned by Chroma is (1 - cosine similarity): 0 = identical,
lower = more relevant. Good matches are typically well below 0.5.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chunking import chunk_text  # noqa: E402
from ingest import load_documents  # noqa: E402

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "ucsc_dining"
DB_PATH = str(Path(__file__).resolve().parent.parent / "chroma_db")

_model = None


def get_model():
    """Lazily load the sentence-transformers embedding model (cached)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _client():
    import chromadb
    return chromadb.PersistentClient(path=DB_PATH)


def build_index(verbose: bool = True) -> int:
    """(Re)build the ChromaDB collection from the documents/ folder.

    Drops any existing collection, then loads -> chunks -> embeds -> stores.
    Returns the number of chunks indexed.
    """
    documents = load_documents()
    if not documents:
        raise RuntimeError("No documents found in documents/ — nothing to index.")

    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []
    for doc_i, doc in enumerate(documents):
        for chunk in chunk_text(doc.text, doc.source, doc.url):
            ids.append(f"{doc_i:02d}_{chunk.chunk_index:03d}")
            texts.append(chunk.text)
            metadatas.append(
                {
                    "source": doc.source,
                    "url": doc.url,
                    "chunk_index": chunk.chunk_index,
                }
            )

    if verbose:
        print(f"Embedding {len(texts)} chunks from {len(documents)} documents...")
    # Prepend the source label to each chunk *for embedding only* (the stored
    # document text stays clean). Chunks lose document-level context after
    # splitting — e.g. a bare "Gabriella Cafe: Italian..." list item no longer
    # signals "off-campus restaurant". Re-injecting the source label restores
    # that topical signal so queries match the right document, not just shared
    # words (contextual chunk headers).
    embed_texts = [f"{meta['source']}. {text}" for meta, text in zip(metadatas, texts)]
    embeddings = get_model().encode(
        embed_texts, normalize_embeddings=True, show_progress_bar=verbose
    ).tolist()

    client = _client()
    # Start clean so re-running never duplicates or mixes stale chunks.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    if verbose:
        print(f"Stored {collection.count()} chunks in ChromaDB at {DB_PATH}")
    return collection.count()


def get_collection():
    """Return the existing collection, or raise if the index isn't built yet."""
    try:
        return _client().get_collection(COLLECTION_NAME)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Vector store not found. Build it first: python run_index.py"
        ) from exc


@dataclass
class Result:
    text: str
    source: str
    url: str
    chunk_index: int
    distance: float


def retrieve(query: str, k: int = 5) -> list[Result]:
    """Return the k chunks closest to ``query`` (lowest cosine distance first)."""
    query_embedding = get_model().encode(
        [query], normalize_embeddings=True
    ).tolist()
    response = get_collection().query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    results: list[Result] = []
    for text, meta, dist in zip(
        response["documents"][0],
        response["metadatas"][0],
        response["distances"][0],
    ):
        results.append(
            Result(
                text=text,
                source=meta.get("source", ""),
                url=meta.get("url", ""),
                chunk_index=meta.get("chunk_index", -1),
                distance=dist,
            )
        )
    return results
