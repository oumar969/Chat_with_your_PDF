import unittest
from io import BytesIO
from rag import extract_pdf, split_page


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
