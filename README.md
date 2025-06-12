# RAG-APP

A local-first Retrieval-Augmented Generation (RAG) chatbot that can process and interact with multiple data sources including documents and websites. RAG-APP is designed for privacy, extensibility, and ease of use, leveraging only free and open-source technologies.

---

## Features

- **Multi-source ingestion:** PDF, DOCX, TXT, web pages (static/dynamic)
- **RAG Engine:** Combines semantic search (vector DB) with LLMs for grounded, factual answers
- **Conversational memory:** Maintains chat history for context-aware responses
- **Source citation:** Returns sources for each answer, increasing transparency
- **Web UI:** Modern, interactive chat interface (HTML/JS/CSS)
- **Extensible:** Modular ingestion and core logic for easy extension
- **Local & Private:** Runs fully locally, no cloud dependencies (except optional web search)

---

## Tech Stack & Major Dependencies

| Purpose/Component         | Library/Tool Used                                      |
|--------------------------|--------------------------------------------------------|
| **API & Backend**        | [FastAPI](https://fastapi.tiangolo.com/)               |
| **Web UI**               | HTML, CSS, JavaScript (custom, in `static/` & `templates/`) |
| **RAG Orchestration**    | [LangChain](https://www.langchain.com/)                |
| **Vector Database**      | [ChromaDB](https://www.trychroma.com/)                 |
| **Embeddings**           | [Sentence Transformers](https://www.sbert.net/) via LangChain |
| **LLM Inference**        | [Ollama](https://ollama.ai/) (local LLM runtime)       |
| **Document Ingestion**   | [PyPDF2](https://pypi.org/project/PyPDF2/), [python-docx](https://python-docx.readthedocs.io/), [Markdown](https://python-markdown.github.io/), [txt] |
| **Web Scraping**         | [Playwright](https://playwright.dev/python/)           |
| **Image OCR**            | [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) |
| **Database Ingestion**   | [SQLAlchemy](https://www.sqlalchemy.org/)    |
| **Environment Variables**| [python-dotenv](https://pypi.org/project/python-dotenv/) |
| **Testing**              | [pytest](https://docs.pytest.org/)                     |
| **Logging**              | Python `logging` module                                |

---

## Architecture

```
RAG-APP/
├── app/
│   ├── api/            # FastAPI routes (chat, ingestion)
│   ├── core/           # Core RAG logic (engine, chat, ingestion, logger)
│   ├── ingestion/      # Data loaders (documents, web, images)
│   ├── static/         # Static files for web UI (CSS, JS)
│   ├── templates/      # HTML templates for web UI
├── data/               # Vector store, sample docs/images
├── uploads/            # User-uploaded files
├── logs/               # Log files
├── test_*.py           # Test scripts
├── requirements.txt    # Python dependencies
├── README.md           # This file
```

**Main Components:**
- **`main.py`**: FastAPI entrypoint, serves API and web UI
- **`core/rag_engine.py`**: Main RAG engine (LLM, embeddings, vector store, memory, chain)
- **`core/engine_singleton.py`**: Singleton pattern for engine instance
- **`core/ingestion.py`**: File/web ingestion logic
- **`core/chat.py`**: Chat orchestration and formatting
- **`ingestion/`**: Data loaders for document and web
- **`api/`**: FastAPI routers for chat and ingestion endpoints
- **`static/`, `templates/`**: Web UI assets

---

## How it Works

1. **Ingestion:** Users upload files or provide URLs. Each is processed and embedded into a vector store (ChromaDB).
2. **Chat:** User asks a question via the web UI. The backend:
   - Retrieves relevant chunks from the vector DB (Relevance is a normalized score, typically between 0 to 1 derived from the similarity between the user's question embedding and each chunk's embedding in ChromaDB, with higher values indicating greater relevance. This is handled automatically by the vector search and LangChain integration.)
   - Passes context to the LLM (Ollama or other local models)
   - Returns an answer with cited sources
3. **Web UI:** Interactive chat interface, file upload, and source display

---

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) (for local LLM inference)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (for image-to-text)
- [Playwright](https://playwright.dev/python/) (for dynamic web scraping)
- Git (for version control)

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [repository-url]
   cd RAG-APP
   ```
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Install Playwright browsers:**
   ```bash
   playwright install
   ```
5. **Set up Ollama:**
   - Install Ollama from https://ollama.ai/
   - Pull the required model:
     ```bash
     ollama pull llama2:7b
     # or
     ollama pull mixtral:8x7b
     ```
6. **Create a .env file:**
   ```bash
   cp .env.example .env
   # Edit as needed
   ```
7. **Run the app:**
   ```bash
   uvicorn app.main:app --reload
   ```
8. **Access the web UI:**
   - Open [http://localhost:8000](http://localhost:8000) in your browser

---

## Usage

- **Upload documents or provide URLs** via the web UI
- **Ask questions** in natural language
- **Get answers** with cited sources and conversational context
- **Review logs** in the `logs/` directory for debugging

---

## Testing

- Run scenario and API tests:
  ```bash
  pytest test_rag_scenarios.py
  pytest test_api.py
  ```

---

## Extending & Customization

- **Add new loaders:** Place new ingestion logic in `app/ingestion/`
- **Add new LLMs or embeddings:** Edit `app/core/rag_engine.py`
- **Customize UI:** Edit files in `app/templates/` and `app/static/`
- **Change vector DB or storage:** Update `core/rag_engine.py` and config

---

## Troubleshooting

- **Ollama errors:** Ensure Ollama is running and the model is pulled
- **Playwright issues:** Run `playwright install` again
- **Tesseract not found:** Add Tesseract to your system PATH
- **.env issues:** Double-check all required environment variables

---

## License

This project is open-source and available under the MIT License.

---

## Acknowledgements

- [Ollama](https://ollama.ai/)
- [ChromaDB](https://www.trychroma.com/)
- [LangChain](https://www.langchain.com/)
- [Playwright](https://playwright.dev/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

---

## About

**RAG-APP** is designed for privacy, extensibility, and local-first AI. For questions, suggestions, or contributions, please open an issue or pull request on GitHub. 
