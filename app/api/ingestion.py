from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, HttpUrl
import json

from app.ingestion.document_loader import process_document
from app.ingestion.web_loader import process_webpage
from app.ingestion.image_loader import process_image
from app.ingestion.database_loader import process_database
from app.core.engine_singleton import rag_engine
from app.core.ingestion import ingest_file, ingest_web_page
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class WebIngestionRequest(BaseModel):
    """Web page ingestion request model."""
    url: HttpUrl
    is_dynamic: bool = False
    metadata: Optional[Dict[str, Any]] = None

class DatabaseIngestionRequest(BaseModel):
    """Database ingestion request model."""
    connection_string: str
    query: str
    metadata: Optional[Dict[str, Any]] = None

class WebPageRequest(BaseModel):
    url: HttpUrl

@router.post("/upload")
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

@router.post("/document")
async def ingest_document(
    file: UploadFile = File(...),
    metadata: str = Form(default="{}")
):
    """
    Ingest a document file (PDF, DOCX, TXT, MD).
    
    Args:
        file: The uploaded document file
        metadata: JSON string of additional metadata
    """
    try:
        # Parse metadata
        metadata_dict = json.loads(metadata)
        
        # Process the document
        documents = await process_document(file, metadata_dict)
        
        # Add to RAG engine
        await rag_engine.add_documents(
            documents=documents,
            source_type="document",
            metadata=metadata_dict
        )
        
        return {
            "status": "success",
            "message": f"Successfully ingested {file.filename}",
            "document_count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webpage")
async def ingest_webpage(request: WebPageRequest):
    """Ingest content from a web page."""
    logger.info(f"Received web page ingestion request: {request.url}")
    try:
        await ingest_web_page(str(request.url))
        logger.info("Successfully ingested web page")
        return {"message": "Web page ingested successfully"}
    except Exception as e:
        logger.error(f"Failed to ingest web page: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image")
async def ingest_image(
    file: UploadFile = File(...),
    metadata: str = Form(default="{}")
):
    """
    Ingest an image file with captioning.
    
    Args:
        file: The uploaded image file
        metadata: JSON string of additional metadata
    """
    try:
        # Parse metadata
        metadata_dict = json.loads(metadata)
        
        # Process the image
        documents = await process_image(file, metadata_dict)
        
        # Add to RAG engine
        await rag_engine.add_documents(
            documents=documents,
            source_type="image",
            metadata=metadata_dict
        )
        
        return {
            "status": "success",
            "message": f"Successfully ingested image: {file.filename}",
            "document_count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database")
async def ingest_database(request: DatabaseIngestionRequest):
    """
    Ingest data from a database query.
    
    Args:
        request: DatabaseIngestionRequest object containing connection and query details
    """
    try:
        # Process the database query
        documents = await process_database(
            connection_string=request.connection_string,
            query=request.query
        )
        
        # Add to RAG engine
        await rag_engine.add_documents(
            documents=documents,
            source_type="database",
            metadata=request.metadata
        )
        
        return {
            "status": "success",
            "message": "Successfully ingested database query results",
            "document_count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 