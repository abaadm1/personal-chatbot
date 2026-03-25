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
| `src/app.py` | **Streamlit web UI** — chat layout, quick prompts, hidden sidebar, optional avatar |
| `src/qa_chain_cli.py` | CLI Q&A (run from `src/` so imports resolve) |
| `src/extra_qa_chains.py` | Extra chain experiments |
| `requirements.txt` | Python dependencies (duplicate copy in `src/requirements.txt` for convenience / Spaces-style layouts; either file is the same set of packages) |

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

### 3. Environment variables

Create a `.env` file where you will **run commands from**: `python-dotenv` loads `.env` from the **current working directory**. Common choices:

- **Project root** (next to `requirements.txt`) if you run `streamlit run src/app.py` from that folder.
- **`src/`** if you prefer `cd src` then `streamlit run app.py` — put `.env` in `src/` in that case.

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes* | Gemini API key |
| `HUGGING_FACE_API_TOKEN` | Yes* | Hugging Face token for **Inference API** embeddings at query time in the Streamlit app |
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

**`app.py`** — centered layout, quick prompts (third-person questions), sidebar hidden via CSS, optional assistant avatar under `src/assets/`.

## Assistant avatar (`app.py`)

Streamlit only accepts a **direct image URL** or a **local file path**, not a gallery page URL.

1. Export your artwork as **PNG** or **JPG** (e.g. from [Vecteezy](https://www.vecteezy.com/vector-art/43182555-robot-emotion-element-chatbot-avatar-chat-bot-character-head-with-feelings-digital-assistant-icon) or your own asset) and respect the provider’s license.
2. Save it as **`src/assets/chatbot_avatar.png`** (or `.jpg` / `.jpeg` / `.webp` — see `app.py` for valid filenames).

If no file is present and no env override is set, the default Streamlit assistant icon is used.

## CLI (optional)

From **`src/`**:

```bash
cd src
python qa_chain_cli.py
```

## Roadmap / ideas

- Richer data under `src/data/` and periodic re-ingest  
- Optional “show sources” in the Streamlit UI  
- Job-description fit / alignment flow  
- Deployment (e.g. Hugging Face Spaces / Docker) with secrets on the host, not in the repo  
