# Architecture and operating boundaries

Owner: [oumar969](https://github.com/oumar969)

This is a local, single-process document assistant. The deployment unit is one Streamlit process. It is suitable for a supervised portfolio demo. It is not a public multi-tenant service.

## Responsibilities

| Module | Responsibility |
| --- | --- |
| `app.py` | UI, explicit data-sharing gate, bounded session history, orchestration |
| `settings.py` | Environment configuration, shared resource limits, secret-safe settings |
| `rag.py` | PDF validation, normalized extraction, page-preserving chunks, context selection |
| `storage.py` | Collection ownership and session cleanup around Chroma |
| `ai_service.py` | Bounded structured Gemini request, citation validation, safe errors and timing |
| `ui.py`, `styles.css` | Presentation |

## Data flow

1. Validate PDF signature, bytes and page count. Reject password-protected PDFs without an empty password and documents exceeding the extracted-text limit.
2. Normalize Unicode ligatures and line-end hyphenation. Split within each page into 700-character chunks with 100-character overlap.
3. Embed batches of at most 128 chunks locally. A shared model is protected by a lock. Each browser session owns its Chroma collections; shared backend access is wrapped with ownership checks.
4. Retrieve up to 12 semantic hits. Prioritize phrases quoted in the question, reconstruct page context and deduplicate pages. Supply at most four sources and 24,000 source-text characters total.
5. Only after user consent, send the standalone question and selected text to Gemini. Do not send the full PDF or chat history.
6. Request structured claims with source IDs. Validate each reference against the supplied sources and render references in application code. Reject malformed or missing references rather than displaying an unchecked answer.
7. Show sources even when the provider fails. Keep only the last 20 chat messages. Allow at most one question every 10 seconds per session.

## Resource lifetime

Document collections are deleted on clear/document replacement and via Streamlit's session-scoped resource release callback when the session cache is released. Streamlit controls the exact disconnect/cleanup timing; a closed tab does not imply immediate deletion. Process shutdown releases in-memory collections. Model files remain in `.models/`. Partial indexes are deleted if indexing fails. Collection names are random, and the storage wrapper rejects lookups outside the current session.

No cross-session document cache is used. SHA-256 plus a pipeline version and embedding-model ID invalidate a session's old index when processing changes. This is cache invalidation, not an access-control token.

## Provider behavior

One application request makes at most one SDK generation attempt, with a 60-second client timeout and no provider/model fallback. The provider or network can still fail. The cooldown is local to a session and is not an account spending cap or a distributed rate limiter. Billing must stay disabled in the Google account to enforce the user's zero-spend preference.

Application diagnostics contain only a random request ID, status, duration and source count. Raw provider errors, document text, user questions, filenames and API keys are not written by application diagnostics. Secrets are loaded from environment variables or ignored `.env`; the dataclass excludes the key from `repr`.

## What validation does not prove

Citation validation proves that referenced IDs exist. It does not prove that a claim follows from a source. Model instructions reduce prompt injection risk but do not guarantee resistance. Retrieval always returns candidates; there is no calibrated relevance threshold or guarantee that an unanswerable question will be rejected. Scanned PDFs require OCR, and tables/columns may extract incorrectly.

Limits on bytes, pages and extracted characters reduce ordinary misuse but do not sandbox the PDF parser. A malicious compressed PDF can consume resources before post-extraction limits run. Before accepting arbitrary public uploads, isolate parsing in a worker with OS-level memory/time limits, add authentication and account-level rate limits, then measure concurrency and retention behavior. Do not expose this local demo as a public production service without that work.

## Evidence and next evaluation

Offline tests cover parsing failures, context recovery, Unicode normalization, context budgets, provider failure handling, citation structure and collection isolation with real Chroma. They do not establish real-world answer accuracy. Use a held-out set of document questions with expected source pages; measure source recall, supported claims, abstention, latency and failures separately. Synthetic checks are regression evidence, not a production quality score.
