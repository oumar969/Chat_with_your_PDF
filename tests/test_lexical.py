import unittest

from lexical import LexicalIndex
from rag import Chunk, source_pages


class LexicalTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            Chunk("Popper advocated piecemeal social engineering and feedback.", 1, "a"),
            Chunk("Java uses garbage collection.", 2, "a"),
            Chunk("C uses malloc and free.", 3, "a"),
        ]
        self.index = LexicalIndex(self.chunks)

    def test_exact_term_retrieval_and_page_context(self):
        hits = self.index.search("Hvad mente Popper med 'piecemeal social engineering'?")
        self.assertEqual(hits[0], "0")
        self.assertEqual(source_pages(self.chunks, hits, "Popper")[0]["page"], 1)

    def test_single_letter_c_is_preserved(self):
        self.assertEqual(self.index.search("Hvordan frigives hukommelse i C?")[0], "2")

    def test_no_matching_words_returns_no_candidates(self):
        self.assertEqual(self.index.search("astronaut banana"), [])

    def test_empty_index_and_question(self):
        self.assertEqual(LexicalIndex([]).search("Popper"), [])
        self.assertEqual(self.index.search(" "), [])
