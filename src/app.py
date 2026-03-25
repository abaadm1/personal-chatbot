"""
Streamlit UI variant: same RAG + Gemini stack as streamlit_app.py.
Visitors ask about Abaad Murtaza; replies follow qa_prompts (Abaad speaking to recruiters).
"""
import subprocess
import sys
from pathlib import Path
from contextlib import contextmanager
from typing import Iterator, List, Tuple

import os
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain.embeddings.base import Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI

from qa_prompts import PROMPT_TMPL

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HF_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")

EMBED_MODEL_NAME = os.getenv("HUGGING_FACE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL_NAME = os.getenv("LLM_MODEL", "gemini-1.5-flash")

ROOT_DIR = Path(__file__).resolve().parent
INDEX_DIR = ROOT_DIR / "data_index"
PROJECT_ROOT = ROOT_DIR.parent
ASSETS_DIR = ROOT_DIR / "assets"
# Page URL is not a loadable image; export PNG/JPG from Vecteezy and save as chatbot_avatar.png:
# https://www.vecteezy.com/vector-art/43182555-robot-emotion-element-chatbot-avatar-chat-bot-character-head-with-feelings-digital-assistant-icon
_ASSISTANT_AVATAR_FILES = (
    ASSETS_DIR / "chatbot_avatar.png",
    ASSETS_DIR / "chatbot_avatar.jpg",
    ASSETS_DIR / "chatbot_avatar.jpeg",
    ASSETS_DIR / "chatbot_avatar.webp",
)


def _resolve_assistant_avatar() -> str | None:
    """Direct HTTPS URL to an image file, absolute file path, or bundled asset under src/assets/."""
    url = (os.getenv("ASSISTANT_AVATAR_URL") or "").strip()
    if url.startswith(("http://", "https://")):
        return url
    path_env = (os.getenv("ASSISTANT_AVATAR_PATH") or "").strip()
    if path_env:
        p = Path(path_env).expanduser()
        if p.is_file():
            return str(p.resolve())
    for cand in _ASSISTANT_AVATAR_FILES:
        if cand.is_file():
            return str(cand.resolve())
    return None


@contextmanager
def _assistant_chat() -> Iterator[None]:
    av = _resolve_assistant_avatar()
    cm = st.chat_message("assistant", avatar=av) if av else st.chat_message("assistant")
    with cm:
        yield

# Third-person questions visitors ask; the model still answers as Abaad per PROMPT_TMPL.
CONVERSATION_STARTERS: List[Tuple[str, str]] = [
    ("Give a profile overview of Abaad Murtaza.", "Give a profile overview of Abaad Murtaza."),
    ("Who is Abaad Murtaza?", "Who is Abaad Murtaza?"),
    (
        "What is Abaad Murtaza's education background?",
        "What is Abaad Murtaza's education background?",
    ),
    (
        "What are Abaad's main areas of expertise?",
        "What are Abaad's main areas of expertise?",
    ),
    (
        "What technical or programming skills does Abaad have?",
        "What technical or programming skills does Abaad have?",
    ),
    (
        "What work experience or achievements should a recruiter know about Abaad?",
        "What work experience or achievements should a recruiter know about Abaad?",
    ),
]


def _hide_sidebar_css() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stSidebarCollapsedControl"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Abaad's Profile Chatbot",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)
_hide_sidebar_css()


if not INDEX_DIR.exists():
    with st.spinner("Index not found. Building FAISS index (first run)…"):
        proc = subprocess.run(
            [sys.executable, str(ROOT_DIR / "ingest.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            st.error(f"ingest.py failed:\n{proc.stderr}")
            st.stop()


class HFAPIEmbeddings(Embeddings):
    def __init__(self, repo_id: str, token: str | None = None, timeout: float = 120.0):
        self.client = InferenceClient(model=repo_id, token=token, timeout=timeout)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.client.feature_extraction(texts)

    def embed_query(self, text: str) -> List[float]:
        vec = self.client.feature_extraction(text)
        return vec[0] if (isinstance(vec, list) and vec and isinstance(vec[0], list)) else vec


def build_chain_gemini(retriever, _llm_repo, _max_new, _temp, _show_sources):
    if not GOOGLE_API_KEY:
        raise RuntimeError("Set GOOGLE_API_KEY in your .env to use the Gemini inference endpoint.")

    llm = ChatGoogleGenerativeAI(
        model=_llm_repo,
        api_key=GOOGLE_API_KEY,
        temperature=_temp,
        max_output_tokens=_max_new,
        convert_system_message_to_human=True,
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=PROMPT_TMPL,
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=_show_sources,
    )


def _queue_starter_query(full_question: str) -> None:
    st.session_state["_pending_query"] = full_question


def render_sources(docs, show: bool) -> None:
    if not show or not docs:
        return
    st.markdown("**Sources**")
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page", None)
        label = f"{Path(src).name}" + (f" (page {page + 1})" if isinstance(page, int) else "")
        with st.expander(f"{i}. {label}"):
            st.write(d.page_content[:1500] + ("…" if len(d.page_content) > 1500 else ""))


# --- Page ---
hf_token = HF_API_TOKEN
if not hf_token:
    st.warning("Set `HUGGING_FACE_API_TOKEN` in `.env` for embedding API calls.")

# Match streamlit_app.py defaults (no sidebar controls)
k = 4
max_new_tokens = 512
temperature = 0.1
show_sources = False

if "history" not in st.session_state:
    st.session_state.history = []

head_cols = st.columns([1, 0.22])
with head_cols[0]:
    st.title("Abaad's Profile Chatbot")
    st.caption("Ask about Abaad Murtaza’s background—answers use his CV and uploaded documents.")
with head_cols[1]:
    st.write("")  # vertical align
    if st.button("Clear chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()


@st.cache_resource(show_spinner="Loading retriever and model…")
def _load_chain(
    _store_dir: str,
    _embed_repo: str,
    _llm_repo: str,
    _k: int,
    _max_new: int,
    _temp: float,
    _show_sources: bool,
):
    if not Path(_store_dir).exists():
        raise FileNotFoundError(f"FAISS store not found at '{_store_dir}'. Run ingest.py first.")
    embeddings = HFAPIEmbeddings(repo_id=_embed_repo, token=hf_token)
    vs = FAISS.load_local(
        _store_dir,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    retriever = vs.as_retriever(search_kwargs={"k": _k})
    return build_chain_gemini(retriever, _llm_repo, _max_new, _temp, _show_sources)


chain = _load_chain(
    str(INDEX_DIR),
    EMBED_MODEL_NAME,
    LLM_MODEL_NAME,
    k,
    int(max_new_tokens),
    temperature,
    show_sources,
)

st.caption("Quick prompts")
cols = st.columns(3)
for idx, (short_label, full_q) in enumerate(CONVERSATION_STARTERS):
    with cols[idx % 3]:
        st.button(
            short_label,
            key=f"starter_{idx}",
            use_container_width=True,
            on_click=_queue_starter_query,
            args=(full_q,),
        )

st.divider()

# Chat history
for q, a, srcs in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(q)
    with _assistant_chat():
        st.markdown(a)
        render_sources(srcs, show_sources)

user_input = st.chat_input("Ask a question about Abaad Murtaza…")
pending = st.session_state.pop("_pending_query", None)
query = (user_input or "").strip() or (str(pending).strip() if pending else "")

if query:
    with st.spinner("Drafting answer…"):
        try:
            res = chain.invoke({"query": query})
            if isinstance(res, dict):
                answer = res.get("result", "")
                sources = res.get("source_documents", []) if show_sources else []
            else:
                answer, sources = str(res), []
        except Exception as e:
            answer, sources = f"Something went wrong: {e}", []
    st.session_state.history.append((query, answer, sources))
    st.rerun()
