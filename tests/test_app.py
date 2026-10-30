"""UI regression with no model downloads or external API calls."""

import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from settings import ROOT, Settings


class AppTests(unittest.TestCase):
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
