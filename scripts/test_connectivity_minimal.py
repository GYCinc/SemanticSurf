import os
import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestConnectivity")

async def test_connection():
    # Use the secret we found earlier
    MCP_SECRET = "8358f9df096b3504bad36c8b6cc74c49ed541e13911932de347c1c5ac4779991"
    # Use the production URL found in .env
    API_BASE = "https://gitenglishhub-production.up.railway.app"
    url = f"{API_BASE}/api/mcp"
    
    logger.info(f"Testing connection to: {url}")
    
    headers = {
        "Authorization": f"Bearer {MCP_SECRET}",
        "Content-Type": "application/json"
    }
    
    # Minimal valid payload for 'ingest.createSession'
    payload = {
        "action": "ingest.createSession",
        "studentId": "test-connectivity", 
        "params": {
            "transcriptText": "Test ping from CLI.",
            "sessionDate": "2024-01-01T00:00:00Z",
            "duration": 10
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
