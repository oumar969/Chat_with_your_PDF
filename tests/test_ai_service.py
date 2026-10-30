import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from google.genai import errors
from pydantic import ValidationError

from ai_service import ABSTENTION, AnswerError, AnswerPayload, generate_answer, render_answer
from settings import Settings


class AnswerTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(api_key="test-secret")
        self.sources = [{"page": 4, "text": "Small changes allow feedback."}]
        self.factory = MagicMock()
        self.client = self.factory.return_value.__enter__.return_value

    def respond(self, payload):
        self.client.models.generate_content.return_value = SimpleNamespace(text=json.dumps(payload))

    def test_valid_structured_answer_and_request_limits(self):
        self.respond({"answerable": True, "claims": [{"text": "Små ændringer giver feedback.", "source_ids": [1]}]})
        with self.assertLogs("ai_service", level="INFO") as logs:
            answer = generate_answer(self.settings, "Explain", self.sources, client_factory=self.factory)
        self.assertIn("[1]", answer)
        self.assertNotIn("test-secret", " ".join(logs.output))
        self.assertNotIn("Small changes", " ".join(logs.output))
        options = self.factory.call_args.kwargs["http_options"]
        self.assertEqual(options.retry_options.attempts, 1)
        request = self.client.models.generate_content.call_args.kwargs
        self.assertEqual(json.loads(request["contents"])["sources"][0]["id"], 1)

    def test_unknown_citations_never_render(self):
        self.respond({"answerable": True, "claims": [{"text": "An answer", "source_ids": [9]}]})
        with self.assertRaises(AnswerError):
            generate_answer(self.settings, "Explain", self.sources, client_factory=self.factory)

    def test_abstention(self):
        payload = AnswerPayload(answerable=False, claims=[])
        self.assertEqual(render_answer(payload, 1), ABSTENTION)

    def test_abstention_with_claims_is_invalid(self):
        payload = AnswerPayload(answerable=False, claims=[{"text": "claim", "source_ids": [1]}])
        with self.assertRaises(ValueError):
            render_answer(payload, 1)

    def test_missing_citations_rejected(self):
        with self.assertRaises(ValidationError):
            AnswerPayload(answerable=True, claims=[{"text": "claim", "source_ids": []}])

    def test_boolean_citation_rejected(self):
        with self.assertRaises(ValidationError):
            AnswerPayload(answerable=True, claims=[{"text": "claim", "source_ids": [True]}])

    def test_empty_model_output_is_safe(self):
        self.client.models.generate_content.return_value = SimpleNamespace(text="")
        with self.assertRaises(AnswerError):
            generate_answer(self.settings, "Explain", self.sources, client_factory=self.factory)

    def test_no_sources_does_not_call_provider(self):
        self.assertEqual(generate_answer(self.settings, "Explain", [], client_factory=self.factory), ABSTENTION)
        self.factory.assert_not_called()

    def test_missing_key_does_not_call_provider(self):
        with self.assertRaises(AnswerError):
            generate_answer(Settings(), "Explain", self.sources, client_factory=self.factory)
        self.factory.assert_not_called()

    def test_provider_overload_is_sanitized(self):
        self.client.models.generate_content.side_effect = errors.ServerError(
            503, {"message": "test-secret private payload"}
        )
        with self.assertRaises(AnswerError) as error:
            generate_answer(self.settings, "Explain", self.sources, client_factory=self.factory)
        self.assertIn("overbelastet", str(error.exception))
        self.assertNotIn("test-secret", str(error.exception))

    def test_network_failure_is_sanitized(self):
        self.factory.side_effect = ConnectionError("test-secret")
        with self.assertRaises(AnswerError) as error:
            generate_answer(self.settings, "Explain", self.sources, client_factory=self.factory)
        self.assertNotIn("test-secret", str(error.exception))

    def test_context_budget_enforced_before_call(self):
        with self.assertRaises(AnswerError):
            generate_answer(self.settings, "Explain", [{"page": 1, "text": "x" * 24001}], client_factory=self.factory)
        self.factory.assert_not_called()

    def test_secret_not_in_config_repr(self):
        self.assertNotIn("test-secret", repr(self.settings))
