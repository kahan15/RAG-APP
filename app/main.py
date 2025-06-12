import os
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
from app.core.chat import chat, clear_chat_history
from app.core.ingestion import ingest_file, ingest_web_page
from app.core.logger import setup_logger
from app.core.engine_singleton import get_rag_engine

logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot",
    description="A RAG-powered chatbot with document ingestion capabilities",
    version="1.0.0"
)

# Mount static files and templates
static_path = Path("app/static")
templates_path = Path("app/templates")
if not static_path.exists():
    logger.warning(f"Static directory not found at {static_path}, creating it")
    static_path.mkdir(parents=True, exist_ok=True)
if not templates_path.exists():
    logger.warning(f"Templates directory not found at {templates_path}, creating it")
    templates_path.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class ChatRequest(BaseModel):
    question: str
    source_filter: Optional[dict] = None

class WebPageRequest(BaseModel):
    url: HttpUrl

@app.get("/", response_class=HTMLResponse)
async def index():
    """Render the main chat interface."""
    logger.info("Rendering main chat interface")
    try:
        return templates.TemplateResponse("index.html", {"request": {}})
    except Exception as e:
        logger.error(f"Failed to render index page: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# API v1 endpoints
@app.post("/api/v1/chat")
async def process_chat(request: ChatRequest):
    """Process a chat message."""
    logger.info(f"Received chat request: {request.question}")
    try:
        # Get RAG engine instance
        rag_engine = get_rag_engine()
        
        # If no source filter is provided, check if we should use the latest document
        if not request.source_filter:
            # Keywords that might indicate the user wants to query the latest document
            latest_keywords = ["this document", "the document", "this pdf", "the pdf", "this file", "the file"]
            if any(keyword in request.question.lower() for keyword in latest_keywords):
                request.source_filter = {"latest": True}
        
        # Process the chat request
        response = await chat(request.question, request.source_filter)
            
        logger.info("Successfully processed chat request")
        return response
    except Exception as e:
        logger.error(f"Failed to process chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Handle file uploads."""
    logger.info(f"Received {len(files)} files for upload")
    try:
        results = []
        for file in files:
            # Save the file
            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            logger.info(f"Saved file: {file_path}")
            
            # Process the file
            await ingest_file(file_path)
            results.append({"filename": file.filename, "status": "success"})
        
        logger.info("Successfully processed all uploaded files")
        return {"message": "Files uploaded and processed successfully", "results": results}
    except Exception as e:
        logger.error(f"Failed to process uploaded files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ingest/webpage")
async def ingest_webpage(request: WebPageRequest):
    """Ingest content from a web page."""
    logger.info(f"Received web page ingestion request: {request.url}")
    try:
        success = await ingest_web_page(str(request.url))
        if not success:
            raise HTTPException(status_code=400, detail="Failed to ingest web page")
        logger.info("Successfully ingested web page")
        return {"message": "Web page ingested successfully"}
    except Exception as e:
        logger.error(f"Failed to ingest web page: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/clear")
async def clear_history():
    """Clear chat history."""
    logger.info("Received request to clear chat history")
    try:
        clear_chat_history()
        logger.info("Successfully cleared chat history")
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Add compatibility routes for old endpoints
@app.post("/chat")
async def legacy_chat(request: ChatRequest):
    """Legacy endpoint for chat - redirects to v1 endpoint."""
    logger.warning("Using deprecated /chat endpoint, please use /api/v1/chat instead")
    return await process_chat(request)

@app.post("/upload")
async def legacy_upload(files: List[UploadFile] = File(...)):
    """Legacy endpoint for file upload - redirects to v1 endpoint."""
    logger.warning("Using deprecated /upload endpoint, please use /api/v1/upload instead")
    return await upload_files(files)

@app.post("/ingest-webpage")
async def legacy_ingest_webpage(request: WebPageRequest):
    """Legacy endpoint for webpage ingestion - redirects to v1 endpoint."""
    logger.warning("Using deprecated /ingest-webpage endpoint, please use /api/v1/ingest/webpage instead")
    return await ingest_webpage(request)

@app.post("/clear-history")
async def legacy_clear_history():
    """Legacy endpoint for clearing chat history - redirects to v1 endpoint."""
    logger.warning("Using deprecated /clear-history endpoint, please use /api/v1/chat/clear instead")
    return await clear_history()

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    # Ensure vector store directory exists
    Path(os.getenv("CHROMA_PERSIST_DIR", "./data/vector_store")).mkdir(parents=True, exist_ok=True)
    
    # Initialize other necessary directories
    for dir_path in ["./data/documents", "./data/images"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 