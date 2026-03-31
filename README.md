# Personal Profile Chatbot

A retrieval-augmented assistant that answers questions about my profile using local documents, Google Gemini 2.5 Flash for generation, sentence-transformers/all-MiniLM-L6-v2 for embeddings, and FAISS for search. The system uses a professional tone optimized for recruiter interactions.

**Live Demo:** https://abaad-chatbot.streamlit.app/

## Project Structure

| Path | Purpose |
|------|---------|
| `src/data/` | Document storage (.txt, .md, .pdf files for CV, certificates, etc.) |
| `src/data_index/` | Generated FAISS index (created by ingest or first Streamlit run) |
| `src/assets/` | Chat avatars (user.png, chatbot.png) |
| `src/ingest.py` | Builds/refreshes FAISS index from `src/data/` |
| `src/qa_prompts.py` | System prompt template defining tone and behavior |
| `src/app.py` | Streamlit web interface with chat and quick prompts |
| `requirements.txt` | Python dependencies |

## Setup

### 1. Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the project root or `src/` directory:

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key |
| `HUGGING_FACE_API_TOKEN` | Yes | Hugging Face token for embeddings |
| `HUGGING_FACE_EMBEDDING_MODEL` | No | Default: `sentence-transformers/all-MiniLM-L6-v2` |
| `LLM_MODEL` | No | Default: `gemini-1.5-flash` |
| `USER_AVATAR_PATH` | No | Custom user avatar path |
| `ASSISTANT_AVATAR_PATH` | No | Custom assistant avatar path |

**Security:** Add `.env` to `.gitignore` - never commit API keys.

### 4. Build Document Index

**IMPORTANT:** Ensure `src/data/` contains all relevant documents (.txt, .md, .pdf) that will be used for RAG before running this command.

```bash
python src/ingest.py
```

This processes files in `src/data/` and creates the FAISS index in `src/data_index/`. The web app will auto-run this on first load if the index is missing.

## Usage

### Web Interface

```bash
streamlit run src/app.py
```

Features:
- Topic-based quick prompts (Overview, Education, Work Experience, etc.)
- Chat interface with custom avatars
- Professional recruiter-friendly responses
- Automatic index building on first run

## Document Organization

Place your profile documents in `src/data/`. The system supports:
- Text files (.txt, .md)
- PDF files (.pdf)
- Organized by topic (education, work experience, skills, etc.)

## Configuration

The chatbot behavior is controlled by:
- **System Prompt**: `src/qa_prompts.py` - defines tone, response format, and rules
- **Quick Prompts**: Predefined questions organized by topic in `src/app.py`
- **Embedding Model**: Configurable via environment variable
- **LLM Model**: Configurable (Gemini models supported)

## Technical Details

- **Vector Store**: FAISS for efficient similarity search
- **Embeddings**: Hugging Face models (local for ingest, API for queries)
- **LLM**: Google Gemini for response generation
- **Framework**: LangChain Classic for RAG pipeline
- **UI**: Streamlit with custom CSS for professional appearance

## Deployment Considerations

- Use environment variables for all API keys
- Ensure embedding model consistency between ingest and query
- Consider rate limits for Hugging Face Inference API
- Docker support available via included Dockerfile  
