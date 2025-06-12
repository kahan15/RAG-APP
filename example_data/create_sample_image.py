from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_image():
    """Create a sample image with text for OCR testing."""
    # Create a new image with white background
    width = 800
    height = 600
    background_color = (255, 255, 255)
    image = Image.new('RGB', (width, height), background_color)
    
    # Get a drawing context
    draw = ImageDraw.Draw(image)
    
    # Try to use a system font, fallback to default if not found
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except IOError:
        font = ImageFont.load_default()
    
    # Sample text
    text = """RAG System Test Image
    
This is a sample image created for testing
OCR capabilities in our RAG system.

The system should be able to:
1. Extract this text accurately
2. Process it into chunks
3. Store it in the vector database
4. Retrieve it when relevant

This helps test our system's ability
to handle text embedded in images."""
    
    # Draw text in black
    text_color = (0, 0, 0)
    draw.text((50, 50), text, font=font, fill=text_color)
    
    # Save the image
    output_path = os.path.join('example_data', 'sample_text.png')
    image.save(output_path)
    print(f"Sample image created at: {output_path}")

if __name__ == "__main__":
    create_sample_image() 