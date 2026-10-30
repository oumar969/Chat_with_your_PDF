"""PDF extraction and page-preserving chunks; no cloud calls during indexing."""

import re
import unicodedata
from dataclasses import dataclass
from io import BytesIO

from settings import MAX_CONTEXT_CHARS, MAX_PAGES, MAX_TEXT_CHARS, MAX_UPLOAD_BYTES


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int
    filename: str


class DocumentError(ValueError):
    """A document validation message safe to display in the UI."""


def source_pages(chunks: list[Chunk], hit_ids: list[str], question: str, limit: int = 4) -> list[dict]:
    """Retrieve small chunks, but give the model page context around each hit."""
    if not 1 <= limit <= 4:
        raise ValueError("Source limit must be between 1 and 4")
    phrases = re.findall(r"['‘’\"“”]([^'‘’\"“”]{3,})['‘’\"“”]", question)
    pages = {}
    page_indices = {}
    for i, chunk in enumerate(chunks):
        identity = (chunk.filename, chunk.page)
        previous = pages.get(identity, "")
        overlap = next(
            (n for n in range(min(len(previous), len(chunk.text), 100), 19, -1) if previous.endswith(chunk.text[:n])), 0
        )
        pages[identity] = previous + (chunk.text[overlap:] if overlap else (" " if previous else "") + chunk.text)
        page_indices.setdefault(identity, i)
    exact = [
        page_indices[identity]
        for identity, text in pages.items()
        if any(normalize_text(phrase).casefold() in normalize_text(text).casefold() for phrase in phrases)
    ]
    semantic = []
    for hit in hit_ids:
        try:
            index = int(hit)
        except ValueError, TypeError:
            continue
        if 0 <= index < len(chunks):
            semantic.append(index)
    ranked = list(dict.fromkeys(exact + semantic))
    sources = []
    seen = set()
    for index in ranked:
        hit = chunks[index]
        identity = (hit.filename, hit.page)
        if identity in seen:
            continue
        seen.add(identity)
        page_text = pages[identity]
        # Bound unusually dense pages while keeping the selected hit and its lead-in.
        page_budget = MAX_CONTEXT_CHARS // limit
        if len(page_text) > page_budget:
            position = max(0, page_text.find(hit.text))
            for phrase in phrases:
                match = page_text.casefold().find(phrase.casefold())
                if match >= 0:
                    position = match
                    break
            start = min(max(0, position - page_budget // 2), len(page_text) - page_budget)
            page_text = page_text[start : start + page_budget]
        sources.append({"filename": hit.filename, "page": hit.page, "text": page_text})
        if len(sources) == limit:
            break
    return sources


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"(?<=\w)-[ \t]*\r?\n\s*(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def split_page(text: str, size: int = 700, overlap: int = 100) -> list[str]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Ugyldig tekststørrelse eller overlap.")
    text = normalize_text(text)
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def extract_pdf(
    data: bytes, filename: str, *, max_upload_bytes=MAX_UPLOAD_BYTES, max_pages=MAX_PAGES, max_text_chars=MAX_TEXT_CHARS
) -> tuple[list[Chunk], int, int]:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    if len(data) > max_upload_bytes:
        raise DocumentError(f"PDF-filen må højst fylde {max_upload_bytes // (1024 * 1024)} MB.")
    if not data.lstrip().startswith(b"%PDF-"):
        raise DocumentError("Filen er ikke en gyldig PDF.")
    try:
        reader = PdfReader(BytesIO(data))
    except PdfReadError:
        raise DocumentError("PDF-filen er beskadiget eller ugyldig.") from None
    if reader.is_encrypted and not reader.decrypt(""):
        raise DocumentError("PDF-filen er beskyttet med adgangskode.")
    if len(reader.pages) > max_pages:
        raise DocumentError(f"Vælg en PDF med højst {max_pages} sider.")
    chunks = []
    empty_pages = 0
    total_chars = 0
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        total_chars += len(text)
        if total_chars > max_text_chars:
            raise DocumentError("PDF-filen indeholder for meget tekst. Opdel den i mindre dokumenter.")
        parts = split_page(text)
        empty_pages += not bool(parts)
        chunks.extend(Chunk(part, number, filename) for part in parts)
    if not chunks:
        raise DocumentError("Ingen tekst fundet. Scannede PDF-filer kræver OCR, som endnu ikke er understøttet.")
    return chunks, len(reader.pages), empty_pages
