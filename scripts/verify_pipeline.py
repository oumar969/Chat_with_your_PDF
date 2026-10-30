"""Synthetic end-to-end regression; no user documents. Run as a module from project root."""

import argparse
import time
from io import BytesIO

import chromadb
from chromadb.config import Settings as ChromaSettings
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from ai_service import generate_answer
from rag import extract_pdf, source_pages
from settings import ROOT, Settings
from storage import SessionDatabase

TEXTS = [
    "Popper advocated gradual social reforms to solve concrete problems. Feedback allows errors to be corrected. This is piecemeal social engineering.",
    "In C the programmer manages dynamic memory using malloc and free. Forgetting free can cause memory leaks.",
    "Java uses automatic garbage collection to reclaim memory from unreachable objects. Collection is not necessarily immediate.",
]
QUESTIONS = [
    ("Hvad mente Popper med gradvise samfundsforandringer?", 1),
    ("Hvordan frigiver programmoren dynamisk hukommelse i C?", 2),
    ("Hvordan fungerer automatisk hukommelsesstyring i Java?", 3),
]


def fixture_pdf():
    writer = PdfWriter()
    font = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )
    for text in TEXTS:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 40 700 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live", action="store_true", help="Send one synthetic question and selected fixture text to Gemini"
    )
    args = parser.parse_args()
    from sentence_transformers import SentenceTransformer

    settings = Settings.load()
    started = time.monotonic()
    chunks, pages, empty = extract_pdf(fixture_pdf(), "synthetic.pdf")
    assert pages == 3 and empty == 0
    model = SentenceTransformer(
        settings.embedding_model,
        revision=settings.embedding_revision,
        cache_folder=str(ROOT / ".models"),
        local_files_only=True,
    )
    store = SessionDatabase(chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False)))
    try:
        name = store.index_chunks(
            chunks, lambda texts: model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        )
        collection = store.get_collection(name)
        correct = 0
        for question, expected in QUESTIONS:
            result = collection.query(
                query_embeddings=model.encode([question], normalize_embeddings=True).tolist(), n_results=len(chunks)
            )
            sources = source_pages(chunks, result["ids"][0], question, limit=1)
            correct += sources[0]["page"] == expected
        print(f"Synthetic retrieval recall@1: {correct}/{len(QUESTIONS)}")
        assert correct == len(QUESTIONS), "Synthetic retrieval regression"
        if args.live:
            question = "Hvad mente Popper med 'piecemeal social engineering'?"
            sources = source_pages(chunks, ["0"], question, limit=1)
            answer = generate_answer(settings, question, sources)
            assert "[1]" in answer, "Live response did not produce a grounded answer"
            print("Live structured response and citation validation: PASS")
            print(answer)
    finally:
        store.close()
    print(f"Pipeline duration: {time.monotonic() - started:.1f}s (includes model load)")


if __name__ == "__main__":
    main()
