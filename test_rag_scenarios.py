import asyncio
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from app.core.ingestion import ingest_file
from app.core.chat import chat, clear_chat_history
from app.core.engine_singleton import get_rag_engine, reset_rag_engine

# Load environment variables
load_dotenv()

async def cleanup_vector_store():
    """Clean up the vector store data"""
    print("\nCleaning up vector store...")
    vector_store_dir = Path("./data/vector_store")
    if vector_store_dir.exists():
        shutil.rmtree(vector_store_dir)
    print("Vector store cleaned up")

async def test_scenario_1():
    """Test uploading and querying the first document about Paris/Jupiter"""
    print("\n=== Scenario 1: First Document Upload and Query ===")
    
    # Create test document about Paris and Jupiter
    with open("test_doc1.txt", "w") as f:
        f.write("""Paris is the capital city of France and one of the most visited cities in the world.
        It is known for its iconic Eiffel Tower, Louvre Museum, and rich cultural heritage.
        The city is divided by the River Seine and is often called the City of Light.

        Jupiter is the largest planet in our solar system.
        It is a gas giant with a Great Red Spot that is actually a giant storm.
        Jupiter has at least 79 moons, with the four largest being Io, Europa, Ganymede, and Callisto.""")
    
    # Upload first document
    success = await ingest_file(Path("test_doc1.txt"))
    print(f"Document 1 upload {'successful' if success else 'failed'}")
    
    # Test queries about Paris
    print("\nQuerying about Paris:")
    response = await chat("What is Paris known for?")
    print(f"Answer: {response['answer']}")
    
    # Test queries about Jupiter
    print("\nQuerying about Jupiter:")
    response = await chat("Tell me about Jupiter's moons")
    print(f"Answer: {response['answer']}")

async def test_scenario_2():
    """Test uploading and querying the second document about Amazon/Mariana Trench"""
    print("\n=== Scenario 2: Second Document Upload and Query ===")
    
    # Create test document about Amazon and Mariana Trench
    with open("test_doc2.txt", "w") as f:
        f.write("""The Amazon Rainforest is the world's largest tropical rainforest.
        It covers much of northwestern Brazil and extends into Colombia, Peru and other South American countries.
        The Amazon is home to millions of plant and animal species.

        The Mariana Trench is the deepest oceanic trench on Earth.
        Located in the western Pacific Ocean, it reaches a maximum depth of about 11,034 meters.
        The trench is home to unique deep-sea creatures adapted to extreme pressure.""")
    
    # Upload second document
    success = await ingest_file(Path("test_doc2.txt"))
    print(f"Document 2 upload {'successful' if success else 'failed'}")
    
    # Test queries about Amazon
    print("\nQuerying about Amazon Rainforest:")
    response = await chat("Where is the Amazon Rainforest located?")
    print(f"Answer: {response['answer']}")
    
    # Test queries about Mariana Trench
    print("\nQuerying about Mariana Trench:")
    response = await chat("How deep is the Mariana Trench?")
    print(f"Answer: {response['answer']}")

async def test_scenario_3():
    """Test querying both documents after restart without re-uploading"""
    print("\n=== Scenario 3: Query After Restart (No Re-upload) ===")
    
    # Reset the RAG engine to simulate a restart
    reset_rag_engine()
    clear_chat_history()
    
    # Test queries about content from both documents
    print("\nQuerying about Paris (from first document):")
    response = await chat("What is the Eiffel Tower?")
    print(f"Answer: {response['answer']}")
    
    print("\nQuerying about Mariana Trench (from second document):")
    response = await chat("What kind of creatures live in the Mariana Trench?")
    print(f"Answer: {response['answer']}")
    
    # Test cross-document query
    print("\nCross-document query about depths and heights:")
    response = await chat("Compare the depth of the Mariana Trench with Jupiter's size")
    print(f"Answer: {response['answer']}")

async def cleanup():
    """Clean up test files"""
    try:
        os.remove("test_doc1.txt")
        os.remove("test_doc2.txt")
    except Exception as e:
        print(f"Cleanup error: {e}")

async def main():
    try:
        # Ensure we have the GROQ API key
        if not os.getenv("GROQ_API_KEY"):
            print("Error: GROQ_API_KEY environment variable not found")
            return
            
        # Clean up vector store before starting
        await cleanup_vector_store()
        
        # Run all scenarios
        await test_scenario_1()
        await test_scenario_2()
        await test_scenario_3()
        
        # Clean up test files
        await cleanup()
        
    except Exception as e:
        print(f"Error during testing: {e}")
        await cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 