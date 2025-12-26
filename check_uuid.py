import os
import json
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

async def check_students():
    # Load environment properly from gitenglishhub
    WORKSPACE_ROOT = Path(__file__).resolve().parents[0]
    env_path = WORKSPACE_ROOT / "gitenglishhub" / ".env.local"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv()

    SECRET = os.getenv("MCP_SECRET", "")
    BASE_URL = os.getenv("GITENGLISH_API_BASE", "https://gitenglishhub-production.up.railway.app")
    
    if not SECRET:
        print("❌ MCP_SECRET not set")
        return

    url = f"{BASE_URL}/api/mcp"
    headers = {"Authorization": f"Bearer {SECRET}", "Content-Type": "application/json"}
    payload = {"action": "students.list", "studentId": "System", "params": {}}
    
    print(f"📡 Querying Hub API: {url}")
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            data = response.json()
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_students())
