"""Document ingestion for The Unofficial Guide (Milestone 3).

Loads every source file from the documents/ folder, parses an optional
two-line attribution header, and cleans the body down to substantive text
(strips HTML tags, unescapes entities like &amp;/&nbsp;, drops common
forum/review boilerplate, and normalizes whitespace).

Each .txt / .md / .html file may begin with an attribution header so that
source + URL survive into retrieval (addresses the missing-attribution risk
in planning.md):

    SOURCE: Reddit r/UCSC -- best dining hall thread
    URL: https://www.reddit.com/r/UCSC/comments/1n2g02r/best_dining_hallcafe/
    ---
    <pasted content goes here>

If the header is absent, the file name is used as the source label.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

# Folder that holds the raw source files, relative to the repo root.
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"

# File types we know how to load. PDFs are only handled if pdfplumber is installed.
TEXT_SUFFIXES = {".txt", ".md"}
HTML_SUFFIXES = {".html", ".htm"}
PDF_SUFFIXES = {".pdf"}

# Lines that are pure boilerplate on review/forum pages and carry no domain meaning.
# Kept deliberately conservative so we never delete an actual review or opinion.
_BOILERPLATE_LINE = re.compile(
    r"""^\s*(
        reply|share|report|save|award|follow|        # reddit/forum action buttons
        read\s*more|see\s*more|show\s*more|
        log\s*in|sign\s*up|continue\s*reading|
        helpful|thanks|cool|oh\s*no|funny|            # yelp reaction buttons
        \d+\s*(comments?|replies|upvotes?|points?)|   # "12 comments", "3 points"
        useful\s*\d*|
        \d+\s*(likes?|shares?)|
        was\s+this\s+review\s+\.*\?*|
        [‹›»«>•·]+|      # stray nav arrows/bullets: > >> bullets
        check\s*out\b.*|                              # "Check out X" nav links
        check\s+special\s+hours|                      # UCSC dining nav
        what.?s\s+open\s+right\s+now|
        other\s+campus\s+dining\s+options|
        experiencing\s+food\s+insecurity\??
    )\s*$""",
    re.IGNORECASE | re.VERBOSE,
)


@dataclass
class Document:
    """A single cleaned source document plus its attribution metadata."""

    source: str           # human-readable label, e.g. "Reddit r/UCSC -- best dining hall"
    url: str               # original URL or location; "" if unknown
    path: str              # file it was loaded from
    text: str              # cleaned, substantive text

    @property
    def char_len(self) -> int:
        return len(self.text)


class _HTMLTextExtractor(HTMLParser):
    """Pulls visible text out of HTML, dropping non-content tags entirely."""

    # Tags whose *contents* are never substantive page content.
    _SKIP = {"script", "style", "noscript", "svg", "head", "nav",
             "footer", "header", "aside", "form", "button"}
    # Tags that imply a line break so words don't run together.
    _BLOCK = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self._SKIP:
            self._skip_depth += 1
        elif tag in self._BLOCK:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in self._BLOCK:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def _strip_html(raw: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(raw)
    return parser.get_text()


def _looks_like_html(text: str) -> bool:
    return bool(re.search(r"<(p|div|br|span|a|html|body)\b", text, re.IGNORECASE))


def clean_text(raw: str, is_html: bool = False) -> str:
    """Reduce a raw document to substantive text.

    Removes HTML tags, unescapes entities (&amp;, &nbsp;, &#39; ...), drops
    boilerplate action lines, and normalizes whitespace. Safe to call on
    plain text that was pasted from a page.
    """
    text = raw
    if is_html or _looks_like_html(text):
        text = _strip_html(text)

    # Decode HTML entities and normalize non-breaking spaces to regular spaces.
    text = html.unescape(text)
    text = text.replace("\xa0", " ").replace("​", "")
    # Normalize odd Unicode punctuation (e.g. fraction slash in "Porter⁄Kresge").
    text = text.replace("⁄", "/").replace("∕", "/")

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            cleaned_lines.append("")
            continue
        if _BOILERPLATE_LINE.match(line):
            continue
        # Collapse runs of internal whitespace within the line.
        cleaned_lines.append(re.sub(r"[ \t]{2,}", " ", line))

    text = "\n".join(cleaned_lines)
    # Collapse 3+ blank lines down to a single blank line (paragraph break).
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _parse_front_matter(raw: str, fallback_source: str) -> tuple[str, str, str]:
    """Split an optional 'SOURCE:/URL: --- body' header from the body.

    Returns (source, url, body). Falls back to the file name as source.
    """
    source, url = fallback_source, ""
    lines = raw.splitlines()
    header: dict[str, str] = {}
    body_start = 0

    # Only treat the top of the file as a header if it begins with SOURCE:/URL:.
    if lines and re.match(r"^\s*(source|url)\s*:", lines[0], re.IGNORECASE):
        for i, line in enumerate(lines):
            if line.strip() == "---":
                body_start = i + 1
                break
            m = re.match(r"^\s*(source|url)\s*:\s*(.*)$", line, re.IGNORECASE)
            if m:
                header[m.group(1).lower()] = m.group(2).strip()
        source = header.get("source", fallback_source) or fallback_source
        url = header.get("url", "")

    body = "\n".join(lines[body_start:])
    return source, url, body


def _read_pdf(path: Path) -> str | None:
    try:
        import pdfplumber  # optional dependency
    except ImportError:
        print(f"  ! skipping {path.name}: install pdfplumber to load PDFs")
        return None
    text_parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[Document]:
    """Load and clean every supported file in ``documents_dir``."""
    docs: list[Document] = []
    files = sorted(
        p for p in documents_dir.iterdir()
        if p.is_file() and p.name != ".gitkeep"
    )

    for path in files:
        suffix = path.suffix.lower()
        if suffix in PDF_SUFFIXES:
            raw = _read_pdf(path)
            if raw is None:
                continue
            is_html = False
        elif suffix in TEXT_SUFFIXES or suffix in HTML_SUFFIXES:
            raw = path.read_text(encoding="utf-8", errors="replace")
            is_html = suffix in HTML_SUFFIXES
        else:
            print(f"  ! skipping {path.name}: unsupported file type")
            continue

        fallback = path.stem.replace("_", " ").replace("-", " ").strip()
        source, url, body = _parse_front_matter(raw, fallback)
        text = clean_text(body, is_html=is_html)

        if not text:
            print(f"  ! skipping {path.name}: no text left after cleaning")
            continue

        docs.append(Document(source=source, url=url, path=str(path), text=text))

    return docs


if __name__ == "__main__":
    # Quick check: load everything and print one cleaned document to eyeball it.
    loaded = load_documents()
    print(f"Loaded {len(loaded)} document(s) from {DOCUMENTS_DIR}\n")
    if loaded:
        d = loaded[0]
        print(f"=== {d.source} ({d.url or 'no url'}) ===")
        print(d.text[:1500])
