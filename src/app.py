"""
Streamlit UI: RAG + Gemini (FAISS, HF Inference embeddings).
Visitors ask about Abaad Murtaza; replies follow qa_prompts (Abaad speaking to recruiters).
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import subprocess
import sys
import random
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

_USER_AVATAR_FILES = (
    ASSETS_DIR / "user.png",
    ASSETS_DIR / "user.jpg",
    ASSETS_DIR / "user.jpeg",
    ASSETS_DIR / "user.webp",
    ASSETS_DIR / "user_avatar.png",
    ASSETS_DIR / "user_avatar.jpg",
    ASSETS_DIR / "user_avatar.jpeg",
    ASSETS_DIR / "user_avatar.webp",
)
_ASSISTANT_AVATAR_FILES = (
    ASSETS_DIR / "chatbot.png",
    ASSETS_DIR / "chatbot.jpg",
    ASSETS_DIR / "chatbot.jpeg",
    ASSETS_DIR / "chatbot.webp",
    ASSETS_DIR / "chatbot_avatar.png",
    ASSETS_DIR / "chatbot_avatar.jpg",
    ASSETS_DIR / "chatbot_avatar.jpeg",
    ASSETS_DIR / "chatbot_avatar.webp",
)


def _first_existing_file(paths: Tuple[Path, ...]) -> str | None:
    for cand in paths:
        if cand.is_file():
            return str(cand.resolve())
    return None


def _resolve_user_avatar() -> str | None:
    path_env = (os.getenv("USER_AVATAR_PATH") or "").strip()
    if path_env:
        p = Path(path_env).expanduser()
        if p.is_file():
            return str(p.resolve())
    return _first_existing_file(_USER_AVATAR_FILES)


def _resolve_assistant_avatar() -> str | None:
    path_env = (os.getenv("ASSISTANT_AVATAR_PATH") or "").strip()
    if path_env:
        p = Path(path_env).expanduser()
        if p.is_file():
            return str(p.resolve())
    return _first_existing_file(_ASSISTANT_AVATAR_FILES)


@contextmanager
def _user_chat() -> Iterator[None]:
    av = _resolve_user_avatar()
    cm = st.chat_message("user", avatar=av) if av else st.chat_message("user")
    with cm:
        yield


@contextmanager
def _assistant_chat() -> Iterator[None]:
    av = _resolve_assistant_avatar()
    cm = st.chat_message("assistant", avatar=av) if av else st.chat_message("assistant")
    with cm:
        yield

# Topic cards configuration
TOPIC_CARDS = [
    {
        "name": "Overview",
        "icon": "👤",
        "color": "#DBEAFE",
        "text_color": "#1E40AF",
        "description": "Profile summary"
    },
    {
        "name": "Education", 
        "icon": "🎓",
        "color": "#D1FAE5",
        "text_color": "#065F46",
        "description": "Academic background"
    },
    {
        "name": "Work Experience",
        "icon": "💼",
        "color": "#FED7AA",
        "text_color": "#9A3412",
        "description": "Professional experience"
    },
    {
        "name": "Teaching",
        "icon": "📚",
        "color": "#E9D5FF",
        "text_color": "#6B21A8",
        "description": "Teaching experience"
    },
    {
        "name": "Internships",
        "icon": "🏢",
        "color": "#FECACA",
        "text_color": "#991B1B",
        "description": "Industry exposure"
    },
    {
        "name": "Skills & Tools",
        "icon": "🔧",
        "color": "#CFFAFE",
        "text_color": "#164E63",
        "description": "Technical skills"
    },
    {
        "name": "Projects",
        "icon": "🚀",
        "color": "#D9F99D",
        "text_color": "#4D7C0F",
        "description": "Portfolio projects"
    },
    {
        "name": "Certifications",
        "icon": "🏆",
        "color": "#FED7AA",
        "text_color": "#9A3412",
        "description": "Professional certifications"
    },
    {
        "name": "Recommendations",
        "icon": "💬",
        "color": "#FBCFE8",
        "text_color": "#9F1239",
        "description": "LinkedIn recommendations"
    },
    {
        "name": "Soft Skills",
        "icon": "🤝",
        "color": "#CCFBF1",
        "text_color": "#134E4A",
        "description": "Interpersonal skills"
    }
]

# Categorized quick prompts
CATEGORIZED_PROMPTS = {
    "Overview": [
        "What drives Abaad's interest in AI?",
        "How would you summarize Abaad's overall background?",
        "What kind of problems does Abaad enjoy solving?",
        "What languages does Abaad speak?",
        "Where is Abaad currently based?",
        "Is Abaad open to new opportunities?"
    ],
    "Education": [
        "What makes Abaad's academic profile distinctive?",
        "Which courses or research shaped Abaad most?",
        "What is notable about Abaad's education journey?"
    ],
    "Work Experience": [
        "What work experience best reflects Abaad's strengths?",
        "Which responsibilities has Abaad handled professionally?",
        "Which achievements stand out across Abaad's roles?",
        "Which experiences define Abaad's career direction?",
        "What makes Abaad a strong AI candidate?",
        "Why might recruiters find Abaad interesting?"
    ],
    "Teaching": [
        "What teaching experience does Abaad bring?",
        "How does Abaad explain complex ideas clearly?"
    ],
    "Internships": [
        "Which internships were most impactful for Abaad?",
        "What did Abaad gain from industry exposure?"
    ],
    "Skills & Tools": [
        "Which programming languages does Abaad use confidently?",
        "What technical tools does Abaad use most?",
        "Which AI and machine learning skills stand out most?",
        "How strong is Abaad's experience with LLMs?",
        "What combination of skills defines Abaad best?"
    ],
    "Projects": [
        "Which projects best showcase Abaad's capabilities?",
        "What project best demonstrates Abaad's practical thinking?",
        "What projects are most relevant for recruiters?"
    ],
    "Certifications": [
        "Which certifications strengthen Abaad's profile most?"
    ],
    "Recommendations": [
        "What do LinkedIn recommendations say about Abaad?",
        "How do others describe working with Abaad?"
    ],
    "Soft Skills": [
        "What soft skills stand out in Abaad's profile?",
        "Which extracurriculars show leadership or initiative?",
        "What personal qualities stand out beyond academics?"
    ]
}

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


def _app_ui_css() -> None:
    """Sidebar hidden + equal-height quick-prompt buttons (full text, no shortening) + topic cards styling."""
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stSidebarCollapsedControl"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }

            /* Topic pills */
            div[data-testid="stPills"] {
                display: flex !important;
                justify-content: center !important;
                margin: 0.35rem 0 1rem 0 !important;
            }

            div[data-testid="stPills"] > div,
            div[data-testid="stPills"] [role="radiogroup"] {
                display: flex !important;
                flex-wrap: wrap !important;
                justify-content: center !important;
                gap: 0.75rem !important;
            }

            div[data-testid="stPills"] [data-baseweb="tag"] {
                margin: 0 !important;
            }

            /* Quick prompts: only horizontal blocks with exactly 3 columns (not the 2-col header). */
            section.main [data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-child(3)):not(:has(div[data-testid="column"]:nth-child(4))) {
                display: flex !important;
                align-items: stretch !important;
                gap: 0.65rem !important;
            }
            section.main [data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-child(3)):not(:has(div[data-testid="column"]:nth-child(4))) div[data-testid="column"] {
                display: flex !important;
                flex-direction: column !important;
                flex: 1 1 0 !important;
                min-width: 0 !important;
            }
            section.main [data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-child(3)):not(:has(div[data-testid="column"]:nth-child(4))) div[data-testid="column"] .stButton {
                flex: 1 1 auto !important;
                width: 100% !important;
                height: 100% !important;
            }
            section.main [data-testid="stHorizontalBlock"]:has(div[data-testid="column"]:nth-child(3)):not(:has(div[data-testid="column"]:nth-child(4))) .stButton > button {
                height: 100% !important;
                min-height: 7.5rem !important;
                width: 100% !important;
                white-space: normal !important;
                text-align: left !important;
                line-height: 1.35 !important;
                padding: 0.65rem 0.75rem !important;
                align-items: flex-start !important;
                justify-content: flex-start !important;
            }
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
_app_ui_css()


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


def _select_category(category_name: str) -> None:
    try:
        st.session_state.selected_category = category_name
        st.session_state.topic_pills = category_name
        st.session_state.used_prompts = set()
        
        category_prompts = CATEGORIZED_PROMPTS.get(category_name, [])
        
        if len(category_prompts) <= 6:
            st.session_state.current_prompts = category_prompts.copy()
        else:
            st.session_state.current_prompts = random.sample(category_prompts, 6)
    except Exception as e:
        st.error(f"Error selecting category: {e}")
        st.session_state.selected_category = None
        st.session_state.topic_pills = None
        st.session_state.used_prompts = set()
        st.session_state.current_prompts = []


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
max_new_tokens = 1500
temperature = 0.1
show_sources = False

if "history" not in st.session_state:
    st.session_state.history = []

if "topic_pills" not in st.session_state:
    st.session_state.topic_pills = None

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "used_prompts" not in st.session_state:
    st.session_state.used_prompts = set()

if "current_prompts" not in st.session_state:
    st.session_state.current_prompts = []

head_cols = st.columns([1, 0.22])
with head_cols[0]:
    st.title("Abaad's Profile Chatbot")
    st.caption("Ask about Abaad Murtaza's background—answers use his CV and uploaded documents.")
with head_cols[1]:
    if st.button("Clear chat", use_container_width=True):
        st.session_state.history = []
        st.session_state.selected_category = None
        st.session_state.topic_pills = None
        st.session_state.used_prompts = set()
        st.session_state.current_prompts = []
        st.rerun()
    st.markdown('<div style="text-align: right; font-size: 0.6em; color: #666;">Knowledge cutoff: April 2026</div>', unsafe_allow_html=True)

def _on_topic_pill_change() -> None:
    try:
        selected = st.session_state.get("topic_pills")
        
        if selected:
            _select_category(selected)
        else:
            st.session_state.selected_category = None
            st.session_state.topic_pills = None
            st.session_state.used_prompts = set()
            st.session_state.current_prompts = []
    except Exception as e:
        st.error(f"Error in topic selection: {e}")
        # Reset state on error
        st.session_state.selected_category = None
        st.session_state.topic_pills = None
        st.session_state.used_prompts = set()
        st.session_state.current_prompts = []


def render_topic_badges() -> None:
    topic_lookup = {topic["name"]: topic for topic in TOPIC_CARDS}
    topic_names = [topic["name"] for topic in TOPIC_CARDS]

    st.pills(
        "Topics",
        options=topic_names,
        selection_mode="single",
        key="topic_pills",
        format_func=lambda name: f"{topic_lookup[name]['icon']}  {name}",
        label_visibility="collapsed",
        on_change=_on_topic_pill_change,
    )

# Call function
render_topic_badges()


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

# Dynamic quick prompts section
if st.session_state.selected_category:
    st.caption(f"Quick prompts related to {st.session_state.selected_category}")
else:
    st.caption("Select a topic badge above to see related prompts")

if st.session_state.current_prompts:
    cols = st.columns(3)
    for idx, prompt in enumerate(st.session_state.current_prompts):
        with cols[idx % 3]:
            st.button(
                prompt,
                key=f"quick_prompt_{idx}",
                use_container_width=True,
                on_click=_queue_starter_query,
                args=(prompt,),
            )
else:
    st.info("No prompts available. Select a topic badge to get started.")

st.divider()

# Chat history
for q, a, srcs in st.session_state.history:
    with _user_chat():
        st.markdown(q)
    with _assistant_chat():
        st.markdown(a)
        render_sources(srcs, show_sources)

user_input = st.chat_input("Ask a question about Abaad Murtaza…")
pending = st.session_state.pop("_pending_query", None)
query = (user_input or "").strip() or (str(pending).strip() if pending else "")

if query:
    # Mark this prompt as used if it's from quick prompts
    if query in st.session_state.current_prompts:
        st.session_state.used_prompts.add(query)
        # Remove from current prompts
        st.session_state.current_prompts.remove(query)
        
        # Add new prompt from the same category if available
        if st.session_state.selected_category:
            category_prompts = CATEGORIZED_PROMPTS.get(st.session_state.selected_category, [])
            available_prompts = [p for p in category_prompts if p not in st.session_state.used_prompts and p not in st.session_state.current_prompts]
            
            if available_prompts:
                new_prompt = random.choice(available_prompts)
                st.session_state.current_prompts.append(new_prompt)
    
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
