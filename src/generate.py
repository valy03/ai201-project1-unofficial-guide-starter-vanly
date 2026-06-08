"""Grounded generation for The Unofficial Guide (Milestone 5).

Pipeline stage 5: take the user's question, retrieve the top-k chunks, and
send question + chunks to Groq (Llama) with a grounding prompt that forces
the model to answer ONLY from the retrieved context and cite its sources.

The grounding is enforced two ways:
  1. System prompt: answer only from the numbered passages; if the answer is
     not present, say so; cite passages by their bracket number.
  2. Structure: each passage is numbered and labeled with its source, and the
     answer is returned alongside the source list so attribution is visible.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

from vector_store import Result, retrieve  # noqa: E402

load_dotenv()

# Groq production model. Swap here if Groq deprecates it (see console.groq.com/docs/models).
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

SYSTEM_PROMPT = """You are The Unofficial Guide to dining at UC Santa Cruz. \
You answer questions about campus dining halls, meal plans and currency \
(Slug Points, Banana Bucks, Flexi Dollars), and off-campus restaurants, using \
real student reviews and official info.

Rules:
- Answer ONLY using the numbered context passages provided. Do not use outside knowledge.
- If the passages do not contain the answer, say you don't have that information \
in your sources. Do not guess prices, hours, or facts.
- Cite the passages you rely on with their bracket numbers, e.g. [1], [3].
- When sources disagree (e.g. opinions about a dining hall), reflect that range \
rather than picking one.
- Be concise and specific."""

_client = None


def _get_client():
    """Lazily construct the Groq client; fail clearly if the key is missing."""
    global _client
    if _client is None:
        from groq import Groq
        key = os.getenv("GROQ_API_KEY")
        if not key or key == "your_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to .env (get a free key at "
                "https://console.groq.com)."
            )
        _client = Groq(api_key=key)
    return _client


def _format_context(results: list[Result]) -> str:
    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(f"[{i}] (Source: {r.source}) {r.text}")
    return "\n\n".join(blocks)


def answer(query: str, k: int = TOP_K) -> tuple[str, list[Result]]:
    """Retrieve context, ground the LLM on it, and return (answer, sources)."""
    results = retrieve(query, k=k)
    if not results:
        return "I don't have any sources to answer that.", []

    user_message = (
        f"Context passages:\n\n{_format_context(results)}\n\n"
        f"Question: {query}"
    )
    completion = _get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content, results


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which dining hall do students think is best?"
    text, sources = answer(q)
    print(f"Q: {q}\n")
    print(text)
    print("\nSources:")
    for i, r in enumerate(sources, 1):
        print(f"  [{i}] {r.source}  (distance {r.distance:.2f})  {r.url}")
