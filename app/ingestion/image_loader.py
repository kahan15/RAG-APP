from typing import List, Dict, Any
from fastapi import UploadFile
from langchain.schema import Document
from PIL import Image
from PIL.ExifTags import TAGS
import tempfile
import os
from transformers import pipeline
import torch

# Initialize the image captioning model
device = "cuda" if torch.cuda.is_available() else "cpu"
image_captioner = pipeline(
    "image-to-text",
    model="nlpconnect/vit-gpt2-image-captioning",
    device=device
)

async def process_image(
    file: UploadFile,
    metadata: Dict[str, Any]
) -> List[Document]:
    """
    Process an image file and convert it to a Document object with caption and metadata.
    
    Args:
        file: The uploaded image file
        metadata: Additional metadata to attach to the document
        
    Returns:
        List containing a single Document object
    """
    # Save file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Open image and extract EXIF data
        image = Image.open(temp_file_path)
        exif_data = extract_exif_data(image)
        
        # Generate image caption
        captions = image_captioner(temp_file_path)
        
        # Combine all captions into a detailed description
        description = " ".join([caption["generated_text"] for caption in captions])
        
        # Create document content combining caption and technical details
        content = f"""Image Description:
{description}

Technical Details:
- Resolution: {image.size[0]}x{image.size[1]}
- Format: {image.format}
- Mode: {image.mode}
"""
        
        # Combine all metadata
        combined_metadata = {
            **metadata,
            "image_metadata": exif_data,
            "filename": file.filename,
            "width": image.size[0],
            "height": image.size[1],
            "format": image.format,
            "mode": image.mode
        }
        
        # Create document
        document = Document(
            page_content=content,
            metadata=combined_metadata
        )
        
        return [document]
    
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

def extract_exif_data(image: Image.Image) -> Dict[str, Any]:
    """Extract EXIF metadata from image."""
    exif_data = {}
    
    try:
        # Get EXIF data
        exif = image._getexif()
        if exif:
            # Convert EXIF tags to readable names
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                # Convert bytes to string if necessary
                if isinstance(value, bytes):
                    try:
                        value = value.decode()
                    except UnicodeDecodeError:
                        value = str(value)
                exif_data[tag] = value
    except (AttributeError, KeyError, IndexError):
        # Image might not have EXIF data
        pass
    
    return exif_data 