import os
from dotenv import load_dotenv
import httpx
import asyncio
import sys

# Load environment variables
load_dotenv()

# Configuration
AAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MCP_SECRET = os.getenv("MCP_SECRET")
GITENGLISH_API_BASE = os.getenv("GITENGLISH_API_BASE", "https://www.gitenglish.com") # Default from docs, override with env
WEBHOOK_SECRET = os.getenv("ASSEMBLYAI_WEBHOOK_SECRET")

print("="*60)
print("🔍 GitEnglishHub Pipeline Verification")
print("="*60)

async def verify():
    # 1. Check Environment Variables
    print("\n[1] Environment Variables:")
    
    missing = []
    if not AAI_API_KEY:
        print("  ❌ ASSEMBLYAI_API_KEY is Missing")
        missing.append("ASSEMBLYAI_API_KEY")
    else:
        print(f"  ✅ ASSEMBLYAI_API_KEY found ({AAI_API_KEY[:4]}...)")

    if not MCP_SECRET:
        print("  ❌ MCP_SECRET is Missing")
        missing.append("MCP_SECRET")
    else:
        print(f"  ✅ MCP_SECRET found ({MCP_SECRET[:4]}...)")
        
    if not os.getenv("GITENGLISH_API_BASE"):
         print(f"  ℹ️  GITENGLISH_API_BASE not set, using default: {GITENGLISH_API_BASE}")
    else:
         print(f"  ✅ GITENGLISH_API_BASE found: {GITENGLISH_API_BASE}")

    if not WEBHOOK_SECRET:
        print("  ⚠️  ASSEMBLYAI_WEBHOOK_SECRET is Missing (Needed if using webhooks)")
    else:
        print(f"  ✅ ASSEMBLYAI_WEBHOOK_SECRET found")

    if missing:
        print(f"\n❌ Critical config missing: {', '.join(missing)}")
        return

    # 2. Check GitEnglishHub Connectivity (/api/mcp)
    print(f"\n[2] Checking Connectivity to {GITENGLISH_API_BASE}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 2a. Check /api/mcp (GET)
        mcp_url = f"{GITENGLISH_API_BASE}/api/mcp"
        print(f"  👉 GET {mcp_url}...")
        try:
            resp = await client.get(mcp_url)
            if resp.status_code == 200:
                print(f"  ✅ Success ({resp.status_code})")
                print(f"     Response: {resp.json().get('message')}")
            else:
                print(f"  ❌ Failed ({resp.status_code})")
                print(f"     Response: {resp.text[:100]}")
        except Exception as e:
            print(f"  ❌ Connection Error: {e}")

        # 2b. Check /api/mcp (POST Auth) - Smoke Test
        print(f"  👉 POST {mcp_url} (Auth Check)...")
        try:
            # We don't have a valid studentId usually, but we can try an invalid action to see if Auth passes
            # or try a harmless action if we knew one.
            # Sending NO action should return 400 if Auth passes, 401 if Auth fails.
            resp = await client.post(
                mcp_url, 
                headers={"Authorization": f"Bearer {MCP_SECRET}"}, 
                json={} 
            )
            
            if resp.status_code == 400: # Expected "Missing required field: action"
                 print(f"  ✅ Auth Success (400 Bad Request as expected for empty body)")
            elif resp.status_code == 200:
                 print(f"  ✅ Success (200 OK)")
            elif resp.status_code == 401:
                 print(f"  ❌ Auth Failed (401 Unauthorized) - Check MCP_SECRET")
            else:
                 print(f"  ⚠️ Unexpected Status ({resp.status_code})")
                 print(f"     Response: {resp.text[:100]}")
                 
        except Exception as e:
            print(f"  ❌ Connection Error: {e}")

        # 3. Check Webhook Endpoint Reachability
        webhook_url = f"{GITENGLISH_API_BASE}/api/webhooks/assemblyai"
        print(f"\n[3] Checking Webhook Reachability ({webhook_url})...")
        try:
            # Send without secret -> Should get 401
            resp = await client.post(webhook_url, json={})
            if resp.status_code == 401:
                print(f"  ✅ Endpoint is Reachable (Returned 401 as expected without secret)")
            elif resp.status_code == 404:
                print(f"  ❌ Endpoint Not Found (404) - Deployment might be missing this route")
            else:
                print(f"  ⚠️ Unexpected Status ({resp.status_code})")
        except Exception as e:
            print(f"  ❌ Connection Error: {e}")


if __name__ == "__main__":
    asyncio.run(verify())
