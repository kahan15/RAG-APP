from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.chat import chat, clear_chat_history
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    """Chat request model."""
    question: str
    source_filter: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    sources: list[Dict[str, Any]]

@router.post("/chat")
async def process_chat(request: ChatRequest):
    """Process a chat message."""
    logger.info(f"Processing chat request: {request.question}")
    try:
        response = await chat(request.question, request.source_filter)
        logger.info("Successfully processed chat request")
        return response
    except Exception as e:
        logger.error(f"Failed to process chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-history")
async def clear_history():
    """Clear chat history."""
    logger.info("Clearing chat history")
    try:
        clear_chat_history()
        logger.info("Successfully cleared chat history")
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 