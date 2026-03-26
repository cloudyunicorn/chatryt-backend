from fastapi.testclient import TestClient
import sys
import os

# Ensure the backend app is in the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.main import app

client = TestClient(app)

def test_pydantic():
    print("Testing Pydantic validation...")
    payload = {
        "message": "A" * 2005,
        "session_id": "123",
        "user_id": "123"
    }
    response = client.post("/chat/", json=payload)
    if response.status_code == 422:
        print("✅ Pydantic string validation works! Returning 422 Error.")
    else:
        print(f"❌ Failed. Expected 422, got {response.status_code}")

def test_rate_limit():
    print("\nTesting Rate Limiting...")
    payload = {
        "message": "Short message",
        "session_id": "123",
        "user_id": "123"
    }
    for i in range(12):
        response = client.post("/chat/", json=payload)
        if response.status_code == 429:
            print(f"✅ Rate Limiting works! Blocked on request {i+1} with 429 Error.")
            return
        
    print("❌ Failed. Did not block after 10 requests.")

if __name__ == "__main__":
    test_pydantic()
    test_rate_limit()
