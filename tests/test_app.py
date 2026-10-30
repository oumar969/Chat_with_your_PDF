"""UI regression with no model downloads or external API calls."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from scripts.verify_pipeline import fixture_pdf
from settings import ROOT, Settings


class AppTests(unittest.TestCase):
    def test_lightweight_upload_search_and_consent_gate(self):
        upload = SimpleNamespace(name="fixture.pdf", getvalue=fixture_pdf)
        with (
            patch("settings.Settings.load", return_value=Settings(api_key="test-secret", retrieval_mode="lexical")),
            patch("streamlit.file_uploader", return_value=upload),
            patch("ai_service.generate_answer", return_value="Et kort svar. [1]") as generate,
            patch.dict("sys.modules", {"sentence_transformers": None, "chromadb": None}),
        ):
            app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
            self.assertEqual(len(app.exception), 0)
            app.chat_input[0].set_value("Hvad mente Popper?").run()
            self.assertEqual(len(app.exception), 0)
            generate.assert_not_called()
            self.assertIsNone(app.session_state["document"]["collection"])
            app.checkbox[0].check().run()
            app.session_state["last_request"] = 0
            app.chat_input[0].set_value("Hvad mente Popper?").run()
            self.assertEqual(len(app.exception), 0)
            generate.assert_called_once()
            self.assertIn("[1]", app.session_state["messages"][-1]["content"])

    def test_empty_workspace_has_no_secret_input_and_requires_consent(self):
        with patch("settings.Settings.load", return_value=Settings()):
            app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.text_input), 0)
        self.assertEqual(len(app.checkbox), 1)
        self.assertFalse(app.checkbox[0].value)

    def test_clear_empty_session_is_safe(self):
        with patch("settings.Settings.load", return_value=Settings()):
            app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
            app.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["messages"], [])
