# Verification record — 2026-10-31

Environment: Windows, Python 3.14.2, dependencies captured in `requirements.lock`.

| Check | Observed result |
| --- | --- |
| Offline test suite, including Streamlit AppTest and real Chroma | 34 tests passed |
| Ruff lint and formatting | Passed |
| `pip check` | No broken requirements |
| Synthetic PDF extraction → local embeddings → Chroma → source selection | Expected first page for all 3 fixture questions |
| One live Gemini request using synthetic Popper material | Structured response parsed, source IDs validated, answer returned |

The live test sent only material created for the synthetic fixture. It did not use a user PDF. One successful provider call does not establish availability or a general quality score. The three retrieval checks cover a small, deliberately simple fixture; real-document evaluation is still required.

GitHub Actions is configured to run the offline quality checks on pushes and pull requests. Local results above do not assert that a particular remote workflow run has passed.
