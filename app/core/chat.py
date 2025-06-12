from typing import Dict, Any, Optional
from app.core.engine_singleton import get_rag_engine
from app.core.logger import setup_logger

logger = setup_logger(__name__)

async def chat(
    question: str,
    source_filter: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process a chat message."""
    logger.info(f"Processing chat message: {question}")
    try:
        rag_engine = get_rag_engine()
        
        # Process the question
        response = await rag_engine.query(question, source_filter)
        
        # Format the response
        formatted_response = {
            "answer": response["answer"],
            "sources": []
        }
        
        # Process and format sources
        if "sources" in response:
            for source in response["sources"]:
                source_info = {}
                
                if source.get("source_type") == "web":
                    source_info.update({
                        "type": "web",
                        "url": source.get("url", ""),
                        "title": source.get("title", ""),
                        "relevance": source.get("relevance", 1.0)
                    })
                else:
                    source_info.update({
                        "type": "document",
                        "file": source.get("file", source.get("source", "")),
                        "page": source.get("page", source.get("page_number", "")),
                        "document_id": source.get("document_id", ""),
                        "relevance": source.get("relevance", 1.0)
                    })
                    
                    # Add document metadata if available
                    if source.get("document_id") in rag_engine.document_metadata:
                        source_info["metadata"] = rag_engine.document_metadata[source.get("document_id")]
                
                formatted_response["sources"].append(source_info)
        
        # Add confidence score if no relevant sources found
        if not formatted_response["sources"]:
            formatted_response["confidence"] = 0.0
            formatted_response["answer"] = "I could not find any relevant information in the available documents to answer your question. Please try rephrasing your question or ensure that the relevant document has been uploaded."
        
        return formatted_response
    except Exception as e:
        logger.error(f"Failed to process chat message: {str(e)}", exc_info=True)
        raise

def clear_chat_history() -> None:
    """Clear the chat history."""
    logger.info("Clearing chat history")
    try:
        rag_engine = get_rag_engine()
        if hasattr(rag_engine.chain, 'memory'):
            rag_engine.chain.memory.clear()
        logger.info("Chat history cleared successfully")
    except Exception as e:
        logger.error(f"Failed to clear chat history: {str(e)}", exc_info=True)
        raise 