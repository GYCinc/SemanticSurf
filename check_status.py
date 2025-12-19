import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
TRANSCRIPT_ID = "a7922eda-8633-42bd-a7e5-effc4909d024"

headers = {
    "authorization": API_KEY,
}

response = requests.get(f"https://api.assemblyai.com/v2/transcript/{TRANSCRIPT_ID}", headers=headers)
data = response.json()
print(f"Status: {data.get('status')}")
print(f"Error: {data.get('error')}")
print(f"Model: {data.get('speech_model')}")
