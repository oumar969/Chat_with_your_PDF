"""Streamlit workspace. Provider, configuration, and retrieval are separate modules."""

import hashlib
import logging
import threading
import time

import streamlit as st

from ai_service import AnswerError, generate_answer
from lexical import LexicalIndex
from rag import DocumentError, extract_pdf, source_pages
from settings import MAX_MESSAGES, PIPELINE_VERSION, REQUEST_COOLDOWN_SECONDS, ROOT, Settings
from storage import SessionDatabase
from ui import apply_style, navigation, welcome

settings = Settings.load()
lightweight = settings.retrieval_mode == "lexical"
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
st.set_page_config(page_title="Chat med din PDF", page_icon="📖", layout="wide")
apply_style()


@st.cache_resource
def encoder(model_name, revision):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, revision=revision, cache_folder=str(ROOT / ".models")), threading.Lock()


def embed(texts):
    model, lock = encoder(settings.embedding_model, settings.embedding_revision)
    with lock:
        return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


@st.cache_resource(scope="session", on_release=lambda store: store.close())
def database():
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    return SessionDatabase(chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False)))


def clear_document():
    previous = st.session_state.pop("document", None)
    if previous and previous.get("collection"):
        database().delete_collection(previous["collection"])
    st.session_state.messages = []


def remember(role, content, sources=None):
    st.session_state.messages.append({"role": role, "content": content, "sources": sources or []})
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]


def show_sources(sources):
    with st.expander("Se kilder", expanded=False):
        st.caption("Åbn et uddrag, hvis du vil kontrollere svaret.")
        for i, source in enumerate(sources, 1):
            with st.expander(f"[{i}] {source['filename']} · side {source['page']}", expanded=False):
                st.text(source["text"])


navigation()
with st.sidebar:
    st.markdown('<div class="eyebrow">DIT ARBEJDSRUM</div>', unsafe_allow_html=True)
    st.header("Dit dokument")
    st.caption("Et nyt perspektiv starter med en PDF.")
    uploaded = st.file_uploader(
        "Upload en PDF",
        type=["pdf"],
        max_upload_size=5 if lightweight else 20,
        key=f"pdf-{st.session_state.get('upload_version', 0)}",
    )
    if not settings.api_key:
        st.info("AI-svar er endnu ikke konfigureret. Du kan stadig søge i dokumentet.")
    consent = st.checkbox("Jeg accepterer, at mit spørgsmål og relevante tekstuddrag sendes til Google.")
    if lightweight:
        st.caption("Let testversion: ord- og frasesøgning · højst 5 MB og 60 sider.")
    st.caption(
        "Brug offentlige øvelsesdokumenter. PDF og søgeindeks behandles lokalt; udvalgte uddrag sendes ved spørgsmål."
    )
    if st.button("Ryd dokument og samtale"):
        clear_document()
        st.session_state.upload_version = st.session_state.get("upload_version", 0) + 1
        st.rerun()
    st.divider()
    st.caption("Udviklet af oumar969 · Chat med din PDF")

st.session_state.setdefault("messages", [])
if uploaded is None:
    if "document" in st.session_state:
        clear_document()
    welcome(max_pages=60 if lightweight else 200, max_mb=5 if lightweight else 20)
    st.stop()

data = uploaded.getvalue()
fingerprint = hashlib.sha256(
    data
    + uploaded.name.encode()
    + (PIPELINE_VERSION + settings.embedding_model + settings.embedding_revision + settings.retrieval_mode).encode()
).hexdigest()
if st.session_state.get("document", {}).get("hash") != fingerprint:
    clear_document()
    try:
        with st.spinner(
            "Læser PDF og bygger søgeindeks …"
            if lightweight
            else "Læser PDF og bygger lokalt søgeindeks. Første gang hentes en gratis sprogmodel …"
        ):
            limits = (
                {"max_upload_bytes": 5 * 1024 * 1024, "max_pages": 60, "max_text_chars": 300_000} if lightweight else {}
            )
            chunks, pages, empty = extract_pdf(data, uploaded.name, **limits)
            lexical_index = LexicalIndex(chunks) if lightweight else None
            collection_name = None if lightweight else database().index_chunks(chunks, embed)
            st.session_state.document = {
                "hash": fingerprint,
                "collection": collection_name,
                "pages": pages,
                "empty": empty,
                "chunks": len(chunks),
                "texts": chunks,
                "lexical_index": lexical_index,
            }
    except DocumentError as exc:
        st.error(f"PDF-filen kunne ikke klargøres: {exc}")
        st.stop()
    except Exception as exc:
        logger.error("index_failed type=%s", type(exc).__name__)
        st.error("Dokumentet kunne ikke klargøres. Prøv en anden PDF eller prøv igen om lidt.")
        st.stop()

doc = st.session_state.document
st.subheader("Dit dokument, i samtale.")
st.caption(f"{uploaded.name} · {doc['pages']} sider · {doc['chunks']} tekstuddrag · lokalt søgeindeks")
if doc["empty"]:
    st.warning(f"{doc['empty']} sider indeholder ingen læsbar tekst. Indhold på disse sider indgår ikke i søgningen.")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.text(message["content"])
        if message.get("sources"):
            show_sources(message["sources"])
if settings.api_key and not consent:
    st.info(
        "Vil du have et kort AI-svar? Sæt flueben ved accept af deling med Google i dokumentmenuen. Indtil da får du kun en liste over kilder."
    )

question = st.chat_input("Stil et spørgsmål — få et kort og konkret svar.", max_chars=2000)
if question and question.strip():
    question = question.strip()
    now = time.monotonic()
    if now - st.session_state.get("last_request", -REQUEST_COOLDOWN_SECONDS) < REQUEST_COOLDOWN_SECONDS:
        st.info("Vent et øjeblik, før du stiller næste spørgsmål.")
        st.stop()
    st.session_state.last_request = now
    remember("user", question)
    with st.chat_message("user"):
        st.text(question)
    with st.chat_message("assistant"):
        sources = []
        try:
            with st.spinner("Finder relevante sider …"):
                if lightweight:
                    hit_ids = doc["lexical_index"].search(question)
                else:
                    collection = database().get_collection(doc["collection"])
                    result = collection.query(
                        query_embeddings=embed([question]).tolist(), n_results=min(12, doc["chunks"])
                    )
                    hit_ids = result["ids"][0]
                sources = source_pages(doc["texts"], hit_ids, question)
            if not settings.api_key:
                answer = "Her er de nærmeste tekstuddrag. AI-svar er endnu ikke konfigureret af appens udvikler."
            elif not consent:
                answer = (
                    "Her er de nærmeste tekstuddrag. Acceptér deling i sidepanelet for at få et formuleret AI-svar."
                )
            else:
                with st.spinner("Skriver svar …"):
                    answer = generate_answer(settings, question, sources)
            st.text(answer)
        except AnswerError as exc:
            answer = str(exc)
            st.warning(answer)
        except Exception as exc:
            logger.error("question_failed type=%s", type(exc).__name__)
            answer = "Forbindelsen eller søgningen kunne ikke gennemføres. Prøv igen om lidt."
            st.error(answer)
        if sources:
            show_sources(sources)
        remember("assistant", answer, sources)
