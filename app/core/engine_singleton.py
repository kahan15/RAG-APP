from typing import Optional
from app.core.rag_engine import RAGEngine
import os
from dotenv import load_dotenv
from app.core.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

# Global RAG engine instance
_rag_engine: Optional[RAGEngine] = None

def get_rag_engine() -> RAGEngine:
    """
    Get or create the RAG engine singleton instance.
    
    Returns:
        RAGEngine: The singleton instance of the RAG engine
    """
    global _rag_engine
    
    if _rag_engine is None:
        logger.info("Initializing new RAG engine instance")
        try:
            _rag_engine = RAGEngine(
                model_name="deepseek-r1-distill-llama-70b",
                embedding_model="sentence-transformers/all-mpnet-base-v2",
                chroma_persist_dir="./data/vector_store"
            )
            logger.info("RAG engine instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create RAG engine instance: {str(e)}", exc_info=True)
            raise
    
    return _rag_engine

def reset_rag_engine() -> None:
    """
    Reset the RAG engine singleton instance.
    This will force a new instance to be created on the next get_rag_engine() call.
    """
    global _rag_engine
    
    if _rag_engine is not None:
        logger.info("Resetting RAG engine instance")
        _rag_engine = None 