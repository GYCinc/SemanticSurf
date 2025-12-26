
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env from .env file explicitly
load_dotenv(".env")

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
aai_key: str = os.environ.get("ASSEMBLYAI_API_KEY")

print(f"DEBUG: SUPABASE_URL present: {bool(url)}")
print(f"DEBUG: SUPABASE_KEY present: {bool(key)}")
print(f"DEBUG: ASSEMBLYAI_API_KEY present: {bool(aai_key)}")

if not url or not key:
    print("Error: Supabase credentials missing")
    sys.exit(1)

supabase: Client = create_client(url, key)

response = supabase.table("students").select("*").eq("username", "Francisco").execute()

if response.data:
    student = response.data[0]
    print(f"SUCCESS: Found Francisco. UUID: {student['id']}")
else:
    print("Error: Francisco not found in DB")
