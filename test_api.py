import requests
import json
import time
from requests.exceptions import RequestException

def upload_file(filepath):
    try:
        url = "http://localhost:8000/api/v1/upload"
        files = {"files": open(filepath, "rb")}
        response = requests.post(url, files=files)
        print(f"\nUploading file: {filepath}")
        print(f"Upload response: {json.dumps(response.json(), indent=2)}\n")
        return response.status_code == 200
    except RequestException as e:
        print(f"Error uploading file: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_chat(question):
    try:
        url = "http://localhost:8000/api/v1/chat"
        headers = {"Content-Type": "application/json"}
        data = {"question": question}
        response = requests.post(url, headers=headers, json=data)
        print(f"\nQuestion: {question}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    except RequestException as e:
        print(f"Error making chat request: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def run_tests():
    # Scenario 1: Upload and test first document
    print("=== Scenario 1: Testing with first document ===")
    if upload_file("uploads/test_doc1.txt"):
        time.sleep(2)  # Give time for processing
        test_chat("What is the capital of France and what is it known for?")
        test_chat("What is the largest planet in our solar system and how many moons does it have?")
    
    # Scenario 2: Upload second document and test cross-document queries
    print("\n=== Scenario 2: Testing with second document and cross-document queries ===")
    if upload_file("uploads/test_doc2.txt"):
        time.sleep(2)  # Give time for processing
        test_chat("Tell me about the Amazon Rainforest")
        test_chat("What is deeper: the Mariana Trench or Jupiter's atmosphere?")
    
    print("\nTest completed! Now you can stop and restart the server to test persistence.")

if __name__ == "__main__":
    run_tests()