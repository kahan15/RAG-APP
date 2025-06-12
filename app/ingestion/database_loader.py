from typing import List, Dict, Any
from langchain.schema import Document
from sqlalchemy import create_engine, text
import json
from datetime import datetime

async def process_database(
    connection_string: str,
    query: str
) -> List[Document]:
    """
    Process a database query and convert results to Document objects.
    
    Args:
        connection_string: SQLAlchemy connection string
        query: SQL query to execute
        
    Returns:
        List of Document objects
    """
    # Create database engine
    engine = create_engine(connection_string)
    
    try:
        # Execute query
        with engine.connect() as connection:
            result = connection.execute(text(query))
            
            # Get column names
            columns = result.keys()
            
            # Convert rows to documents
            documents = []
            for row in result:
                # Convert row to dict
                row_dict = dict(zip(columns, row))
                
                # Convert any non-serializable objects to strings
                processed_dict = process_row_values(row_dict)
                
                # Create markdown representation of the row
                content = dict_to_markdown(processed_dict)
                
                # Create metadata
                metadata = {
                    "source_type": "database",
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "row_data": processed_dict
                }
                
                # Create document
                document = Document(
                    page_content=content,
                    metadata=metadata
                )
                
                documents.append(document)
            
            return documents
    
    finally:
        engine.dispose()

def process_row_values(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert non-serializable values to strings."""
    processed = {}
    
    for key, value in row_dict.items():
        if isinstance(value, (datetime, bytes)):
            processed[key] = str(value)
        elif hasattr(value, '_asdict'):  # For custom SQL types
            processed[key] = dict(value._asdict())
        elif hasattr(value, '__dict__'):  # For custom objects
            processed[key] = str(value)
        else:
            try:
                # Test JSON serialization
                json.dumps(value)
                processed[key] = value
            except (TypeError, OverflowError):
                processed[key] = str(value)
    
    return processed

def dict_to_markdown(data: Dict[str, Any], indent: int = 0) -> str:
    """Convert a dictionary to a markdown-formatted string."""
    markdown = []
    prefix = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            markdown.append(f"{prefix}- **{key}**:")
            markdown.append(dict_to_markdown(value, indent + 1))
        elif isinstance(value, (list, tuple)):
            markdown.append(f"{prefix}- **{key}**:")
            for item in value:
                if isinstance(item, dict):
                    markdown.append(dict_to_markdown(item, indent + 1))
                else:
                    markdown.append(f"{prefix}  - {item}")
        else:
            markdown.append(f"{prefix}- **{key}**: {value}")
    
    return "\n".join(markdown) 