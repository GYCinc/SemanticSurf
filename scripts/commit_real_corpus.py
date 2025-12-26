import os
import sys
import asyncio
import json
import logging
import httpx
from pathlib import Path

# Setup paths
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CorpusCommit")

async def commit_corpus():
    MCP_SECRET = "8358f9df096b3504bad36c8b6cc74c49ed541e13911932de347c1c5ac4779991"
    session_id = "3e9a22ff-83ff-4edc-846e-8abc9a66d28b"
    student_id = "Jocelyn"
    
    api_url = "https://gitenglish.com/api/mcp"
    auth_headers = {"Authorization": f"Bearer {MCP_SECRET}", "Content-Type": "application/json"}
    
    # We'll just trigger it with empty words list if we can't find them, 
    # but the API handles the logic. Let's just see the response structure.
    payload = {
        "action": "ingest.commitCorpus",
        "studentId": student_id,
        "params": {"sessionId": session_id, "speaker": "B", "words": []}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(api_url, headers=auth_headers, json=payload)
        result = r.json()
        logger.info(f"📡 API Response: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(commit_corpus())
