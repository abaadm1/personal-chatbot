---
title: My Profile Chatbot
emoji: 🚀
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 8501
tags:
- streamlit
pinned: false
short_description: RAG chatbot over CV and documents — Gemini, FAISS, Streamlit
---

# My Profile Chatbot

A **retrieval-augmented** assistant that answers questions about your profile (skills, education, experience) using **local documents**, **Google Gemini** for generation, and **FAISS** for search. The system prompt in `src/qa_prompts.py` defines tone and behavior (e.g. speaking as you in a recruiter-friendly way).

## Project structure

| Path | Role |
|------|------|
| `src/data/` | Put `.txt`, `.md`, and `.pdf` files to index (CV, certificates, etc.) |
| `src/data_index/` | Generated FAISS index (created by ingest or first Streamlit run) |
| `src/assets/` | Chat avatars (raster images); see **Chat avatars** below |
| `src/ingest.py` | Build / refresh the FAISS index from `src/data/` |
| `src/qa_prompts.py` | Prompt template for the QA chain |
| `src/app.py` | **Streamlit UI** — chat, quick prompts (full questions), avatars, CSS hides sidebar and aligns the 3-column prompt grid |
| `src/qa_chain_cli.py` | CLI Q&A over the same FAISS index (run from `src/`) |
| `src/extra_qa_chains.py` | Extra chain experiments |
| `requirements.txt` | Python dependencies (mirror: `src/requirements.txt`) |

## Setup

### 1. Python virtual environment

```powershell
cd path\to\MyProfileChatbot-main
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

From the **repository root**:

```bash
pip install -r requirements.txt
```

(Alternatively: `pip install -r src/requirements.txt` — same list.)

Always **run Streamlit with this venv active** (or use `venv\Scripts\python.exe -m streamlit …`) so packages like `huggingface_hub` resolve correctly.

The Streamlit app and CLI use **`langchain_classic`** for `RetrievalQA` / prompts; install includes **`langchain-classic`** (see `requirements.txt`).

### 3. Environment variables

Create a `.env` file where you will **run commands from**: `python-dotenv` loads `.env` from the **current working directory**. Common choices:

- **Project root** (next to `requirements.txt`) if you run `streamlit run src/app.py` from that folder.
- **`src/`** if you prefer `cd src` then `streamlit run app.py` — put `.env` in `src/` in that case.

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes* | Gemini API key |
| `HUGGING_FACE_API_TOKEN` | Yes* | Hugging Face token for **Inference API** embeddings at query time in the Streamlit app |
| `HUGGING_FACE_EMBEDDING_MODEL` | No | Default in code: `sentence-transformers/all-MiniLM-L6-v2` |
| `LLM_MODEL` | No | Default in code: `gemini-1.5-flash` (override e.g. `gemini-2.5-flash`) |
| `USER_AVATAR_PATH` | No | Override path to the **user** chat avatar image (otherwise `src/assets/` filenames below) |
| `ASSISTANT_AVATAR_PATH` | No | Override path to the **assistant** avatar (otherwise `src/assets/` filenames below) |

\*Required for the shipped Streamlit + Gemini flow.

**Security:** Do not commit real keys. Add `.env` to `.gitignore` if it is not already ignored.

### 4. Build the document index

From the **project root**:

```bash
python src/ingest.py
```

This reads files under `src/data/`, writes `src/data_index/`, and `embeddings_model.txt` for consistency with retrieval.

> **Note:** `ingest.py` uses **local** `HuggingFaceEmbeddings` (see that file). The Streamlit app uses the **HF Inference API** for embeddings when loading the index, so the embedding model name should stay aligned with what you used at ingest.

If `src/data_index/` is missing, **`src/app.py`** will try to run `ingest.py` automatically on first load (with a spinner).

## Run the web UI

From the **project root**, with the venv activated:

```bash
streamlit run src/app.py
```

Or from **`src/`**:

```bash
cd src
streamlit run app.py
```

**`app.py`** — centered layout, **six quick-prompt buttons** (full questions, not shortened), **sidebar hidden** via CSS, **3-column prompt rows** with equal-height styling, and **avatars** from `src/assets/` when present.

## Chat avatars (`src/assets/`)

Streamlit loads avatars from **local raster images** (PNG, JPG, or WebP). The app uses the first match in each list (same order as in `src/app.py`):

**User**

- `user.png`, `user.jpg`, `user.jpeg`, `user.webp`
- `user_avatar.png`, `user_avatar.jpg`, `user_avatar.jpeg`, `user_avatar.webp`

**Assistant**

- `chatbot.png`, `chatbot.jpg`, `chatbot.jpeg`, `chatbot.webp`
- `chatbot_avatar.png`, `chatbot_avatar.jpg`, `chatbot_avatar.jpeg`, `chatbot_avatar.webp`

The repo is intended to ship with **`user.png`** and **`chatbot.png`**. You can replace them or set **`USER_AVATAR_PATH`** / **`ASSISTANT_AVATAR_PATH`** in `.env`.

**SVG:** `st.chat_message` does not reliably use SVG as an avatar; use PNG/JPG/WebP for the running UI. An optional **`chatbot.svg`** can remain in `src/assets/` only as a source graphic for you to export into `chatbot.png`.

If no file matches for a role, Streamlit’s default icon is used for that role.

## CLI (optional)

From **`src/`** (same `.env` and index as the web app):

```bash
cd src
python qa_chain_cli.py
```

Uses local `HuggingFaceEmbeddings` (from `embeddings_model.txt` in the index) and Gemini, same prompt template as `qa_prompts.py`.

## Roadmap / ideas

- Richer data under `src/data/` and periodic re-ingest  
- Optional “show sources” in the Streamlit UI  
- Job-description fit / alignment flow  
- Deployment (e.g. Hugging Face Spaces / Docker) with secrets on the host, not in the repo  
