"""Server configuration. Never expose secret values through repr or logs."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_PAGES = 200
MAX_TEXT_CHARS = 2_000_000
MAX_CONTEXT_CHARS = 24_000
MAX_MESSAGES = 20
REQUEST_COOLDOWN_SECONDS = 10
PIPELINE_VERSION = "3"


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    model: str = "gemini-3.1-flash-lite"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_revision: str = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"

    @classmethod
    def load(cls):
        local = dotenv_values(ROOT / ".env")
        return cls(
            api_key=(os.getenv("GEMINI_API_KEY") or local.get("GEMINI_API_KEY") or "").strip(),
            model=(os.getenv("GEMINI_MODEL") or local.get("GEMINI_MODEL") or cls.model).strip(),
        )
