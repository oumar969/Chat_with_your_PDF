import unittest
from io import BytesIO
from rag import Chunk, extract_pdf, split_page, source_pages


class ChunkTests(unittest.TestCase):
    def test_no_text_is_lost(self):
        text = " ".join(f"ord{i}" for i in range(500))
        parts = split_page(text)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(part) <= 700 for part in parts))
        for word in text.split():
            self.assertTrue(any(word in part for part in parts))

    def test_empty_page(self):
        self.assertEqual(split_page(" \n\t"), [])

    def test_long_unbroken_text_terminates(self):
        parts = split_page("x" * 2000)
        self.assertEqual(len(parts), 4)
        self.assertTrue(all(len(part) <= 700 for part in parts))

    def test_invalid_overlap(self):
        with self.assertRaises(ValueError):
            split_page("test", size=10, overlap=10)


class ContextTests(unittest.TestCase):
    def test_definition_before_matched_chunk_is_included(self):
        text = "Popper favoured gradual reforms and feedback. " + "context " * 100 + "This is called piecemeal social engineering."
        chunks = [Chunk(part, 4, "book.pdf") for part in split_page(text)]
        sources = source_pages(chunks, [str(len(chunks) - 1)], "What is 'piecemeal social engineering'?")
        self.assertIn("gradual reforms and feedback", sources[0]["text"])
        self.assertEqual(sources[0]["text"], text)

    def test_exact_phrase_ranks_before_semantic_hit_and_pages_deduplicate(self):
        chunks = [Chunk("Unrelated material", 1, "a.pdf"), Chunk("piecemeal social engineering", 4, "a.pdf"), Chunk("Additional context", 4, "a.pdf")]
        sources = source_pages(chunks, ["0", "1", "2"], "Explain ‘piecemeal social engineering’")
        self.assertEqual([s["page"] for s in sources], [4, 1])

    def test_unquoted_query_retains_semantic_order(self):
        chunks = [Chunk("First", 1, "a.pdf"), Chunk("Second", 2, "a.pdf")]
        self.assertEqual(source_pages(chunks, ["1", "0"], "Explain this", limit=1)[0]["page"], 2)


class PdfTests(unittest.TestCase):
    def test_blank_pdf_is_rejected(self):
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        buffer = BytesIO()
        writer.write(buffer)
        with self.assertRaisesRegex(ValueError, "Ingen tekst"):
            extract_pdf(buffer.getvalue(), "blank.pdf")

    def test_password_protected_pdf_is_rejected(self):
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        writer.encrypt("secret")
        buffer = BytesIO()
        writer.write(buffer)
        with self.assertRaisesRegex(ValueError, "adgangskode"):
            extract_pdf(buffer.getvalue(), "locked.pdf")
