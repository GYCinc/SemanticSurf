
import assemblyai as aai
import os
from dotenv import load_dotenv

# Path to your .env.local
load_dotenv("/Users/safeSpacesBro/gitenglishhub/.env.local")

key = os.getenv("ASSEMBLYAI_API_KEY")
print(f"Key found: {key[:5]}...")
aai.settings.api_key = key
print("✅ Setting keys worked")

transcriber = aai.Transcriber()
print("✅ Transcriber initialized")
