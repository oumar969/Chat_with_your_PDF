"""PDF extraction and page-preserving chunks; no cloud calls during indexing."""
from dataclasses import dataclass
from io import BytesIO
import re


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int
    filename: str


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
