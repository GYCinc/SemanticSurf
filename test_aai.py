import os
import assemblyai as aai
from dotenv import load_dotenv

load_dotenv()
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

transcriber = aai.Transcriber()
transcript = transcriber.transcribe("https://storage.googleapis.com/aai-web-samples/news.mp4")
print(f"Status: {transcript.status}")
print(f"Text: {transcript.text[:50]}...")
