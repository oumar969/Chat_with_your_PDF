"""PDF extraction and page-preserving chunks; no cloud calls during indexing."""
from dataclasses import dataclass
from io import BytesIO
import re
import unicodedata


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int
    filename: str


def source_pages(chunks: list[Chunk], hit_ids: list[str], question: str, limit: int = 4) -> list[dict]:
    """Retrieve small chunks, but give the model page context around each hit."""
    phrases = re.findall(r"['‘’\"“”]([^'‘’\"“”]{3,})['‘’\"“”]", question)
    normalize = lambda value: unicodedata.normalize("NFKC", value).casefold()
    exact = [i for i, chunk in enumerate(chunks)
             if any(normalize(phrase) in normalize(chunk.text) for phrase in phrases)]
    ranked = list(dict.fromkeys(exact + [int(hit) for hit in hit_ids]))
    sources = []
    seen = set()
    for index in ranked:
        hit = chunks[index]
        identity = (hit.filename, hit.page)
        if identity in seen:
            continue
        seen.add(identity)
        page_text = ""
        for chunk in chunks:
            if (chunk.filename, chunk.page) != identity:
                continue
            overlap = next((n for n in range(min(len(page_text), len(chunk.text), 100), 0, -1)
                            if page_text.endswith(chunk.text[:n])), 0)
            page_text += chunk.text[overlap:] if overlap else (" " if page_text else "") + chunk.text
        # Bound unusually dense pages while keeping the selected hit and its lead-in.
        if len(page_text) > 12000:
            position = page_text.find(hit.text)
            start = max(0, position - 4000)
            page_text = page_text[start:start + 12000]
        sources.append({"filename": hit.filename, "page": hit.page, "text": page_text})
        if len(sources) == limit:
            break
    return sources


def split_page(text: str, size: int = 700, overlap: int = 100) -> list[str]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Ugyldig tekststørrelse eller overlap.")
    text = re.sub(r"\s+", " ", text).strip()
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


def extract_pdf(data: bytes, filename: str) -> tuple[list[Chunk], int, int]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted and not reader.decrypt(""):
        raise ValueError("PDF-filen er beskyttet med adgangskode.")
    if len(reader.pages) > 200:
        raise ValueError("Vælg en PDF med højst 200 sider i denne første version.")
    chunks = []
    empty_pages = 0
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        parts = split_page(text)
        empty_pages += not bool(parts)
        chunks.extend(Chunk(part, number, filename) for part in parts)
    if not chunks:
        raise ValueError("Ingen tekst fundet. Scannede PDF-filer kræver OCR, som endnu ikke er understøttet.")
    return chunks, len(reader.pages), empty_pages
