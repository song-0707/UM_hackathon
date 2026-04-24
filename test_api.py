import requests
import json
import os

from dotenv import load_dotenv

load_dotenv()

def test_api():
    url = "https://api.ilmu.ai/anthropic/v1/messages"
    api_key = os.getenv("LLM_API_KEY", "your-api-key")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "ilmu-glm-5.1",
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Hello"}]}]
    }
    print(f"Testing API: {url}")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=100)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
