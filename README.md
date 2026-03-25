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
| `src/assets/` | Optional images (e.g. assistant chat avatar) |
| `src/ingest.py` | Build / refresh the FAISS index from `src/data/` |
| `src/qa_prompts.py` | Prompt template for the QA chain |
| `src/streamlit_app.py` | Original Streamlit UI |
| `src/streamlit_app2.py` | Streamlit UI with chat layout, quick prompts, optional custom avatar |
| `src/qa_chain_cli.py` | CLI Q&A (run from `src/` so imports resolve) |
| `requirements.txt` | Python dependencies |

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

```bash
pip install -r requirements.txt
```

Always **run Streamlit with this venv active** (or use `venv\Scripts\python.exe -m streamlit …`) so packages like `huggingface_hub` resolve correctly.

### 3. Environment variables

Create a `.env` file where you will **run commands from**: `python-dotenv` loads `.env` from the **current working directory**. Common choices:

- **Project root** (next to `requirements.txt`) if you run `streamlit run src/streamlit_app2.py` from that folder.
- **`src/`** if you prefer `cd src` then `streamlit run streamlit_app2.py` — put `.env` in `src/` in that case.

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes* | Gemini API key |
| `HUGGING_FACE_API_TOKEN` | Yes* | Hugging Face token for **Inference API** embeddings at query time in the Streamlit apps |
| `HUGGING_FACE_EMBEDDING_MODEL` | No | Default: `sentence-transformers/all-MiniLM-L6-v2` |
| `LLM_MODEL` | No | Default in code: `gemini-1.5-flash` (override e.g. `gemini-2.5-flash`) |
| `ASSISTANT_AVATAR_URL` | No | **Direct URL** to an image file (`.png` / `.jpg`), not an HTML page |
| `ASSISTANT_AVATAR_PATH` | No | Absolute path to a local avatar image |

\*Required for the shipped Streamlit + Gemini flow.

**Security:** Do not commit real keys. Add `.env` to `.gitignore` if it is not already ignored.

### 4. Build the document index

From the **project root**:

```bash
python src/ingest.py
```

This reads files under `src/data/`, writes `src/data_index/`, and `embeddings_model.txt` for consistency with retrieval.

> **Note:** `ingest.py` uses **local** `HuggingFaceEmbeddings` (see that file). The Streamlit apps use the **HF Inference API** for embeddings when loading the index, so the embedding model name should stay aligned with what you used at ingest.

If `src/data_index/` is missing, `streamlit_app.py` / `streamlit_app2.py` will try to run `ingest.py` automatically on first load (with a spinner).

## Run the web UI

From the **project root**, with the venv activated:

```bash
streamlit run src/streamlit_app2.py
```

**`streamlit_app2.py`** — centered layout, quick prompts (third-person questions about you), sidebar hidden, optional assistant avatar under `src/assets/`.

**`streamlit_app.py`** — simpler, earlier UI with a settings sidebar.

## Assistant avatar (`streamlit_app2`)

Streamlit only accepts a **direct image URL** or a **local file path**, not a gallery page URL.

1. Export your artwork as **PNG** or **JPG** (e.g. from [Vecteezy](https://www.vecteezy.com/vector-art/43182555-robot-emotion-element-chatbot-avatar-chat-bot-character-head-with-feelings-digital-assistant-icon) or your own asset) and respect the provider’s license.
2. Save it as **`src/assets/chatbot_avatar.png`** (or `.jpg` / `.jpeg` / `.webp` — see `streamlit_app2.py` for checked names).

If no file is present and no env override is set, the default Streamlit assistant icon is used.

## CLI (optional)

From **`src/`**:

```bash
cd src
python qa_chain_cli.py
```

## Roadmap / ideas

- Richer data under `src/data/` and periodic re-ingest  
- Optional “show sources” UX in `streamlit_app2`  
- Job-description fit / alignment flow  
- Deployment (e.g. Hugging Face Spaces / Docker) with secrets configured in the host, not in the repo  
