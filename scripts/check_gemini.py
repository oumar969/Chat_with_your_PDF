"""Check server credentials without printing secrets."""
import os
from pathlib import Path

from dotenv import dotenv_values
from google import genai
from google.genai import errors, types

config = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
key = (os.getenv("GEMINI_API_KEY") or config.get("GEMINI_API_KEY") or "").strip()
print("Key configured:", bool(key))
if not key:
    raise SystemExit(1)
model = os.getenv("GEMINI_MODEL") or config.get("GEMINI_MODEL") or "gemini-3.8-flash"
print("Model:", model)
try:
    with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60000)) as client:
        response = client.models.generate_content(
            model=model,
            contents="Reply only: OK",
            config=types.GenerateContentConfig(max_output_tokens=512),
        )
    print("Gemini connection: OK" if response.text else "Gemini connected, no text returned")
except errors.APIError as exc:
    print("Gemini API status:", exc.code)
    print("API message:", str(exc.message).replace(key, "[REDACTED]"))
    if exc.code == 404:
        with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=15000)) as client:
            for available in client.models.list():
                if "generateContent" in (available.supported_actions or []):
                    print("Available model:", available.name)
    raise SystemExit(2)
except Exception as exc:
    print("Connection error type:", type(exc).__name__)
    raise SystemExit(3)
