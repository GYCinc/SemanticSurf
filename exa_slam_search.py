import requests
import json

EXA_API_KEY = "758d3439-a850-4818-9f47-485d8b3d5415"
EXA_ENDPOINT = "https://api.exa.ai/search"

def deep_dive(query):
    headers = {"x-api-key": EXA_API_KEY, "Content-Type": "application/json"}
    payload = {
        "query": query,
        "numResults": 5,
        "useAutoprompt": True,
        "contents": {"text": True}
    }
    response = requests.post(EXA_ENDPOINT, headers=headers, json=payload)
    data = response.json()
    for result in data.get("results", []):
        print(f"\n--- {result.get('url')} ---")
        text = result.get('text', '')
        if "slam-1" in text.lower() and ("punctuate" in text.lower() or "speaker" in text.lower()):
             print(text[:2000])

if __name__ == "__main__":
    deep_dive('AssemblyAI "slam-1" speaker_labels punctuate false')

