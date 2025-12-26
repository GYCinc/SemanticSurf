import os
from dotenv import load_dotenv
import assemblyai as aai

# Load environment
env_path = "/Users/safeSpacesBro/AssemblyAIv2/gitenglishhub/.env.local"
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv()

AAI_API_KEY = os.getenv("AAI_API_KEY")
if not AAI_API_KEY:
    print("❌ AAI_API_KEY not found")
    exit(1)

aai.settings.api_key = AAI_API_KEY

def list_transcripts():
    print("🔍 Fetching recent transcripts from AssemblyAI...")
    try:
        # The SDK doesn't have a direct 'list' on Transcriber in the way I might expect, 
        # but let's check the API directly if needed or use the SDK's methods.
        import httpx
        headers = {"authorization": AAI_API_KEY}
        response = httpx.get("https://api.assemblyai.com/v2/transcript?limit=5", headers=headers)
        data = response.json()
        
        if "transcripts" in data:
            for t in data["transcripts"]:
                print(f"ID: {t['id']} | Status: {t['status']} | Created: {t['created']}")
        else:
            print("No transcripts found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_transcripts()
