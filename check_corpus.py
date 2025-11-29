import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Get the last 10 entries from student_corpus
res = supabase.table("student_corpus").select("*").order("created_at", desc=True).limit(10).execute()

print(f"Last {len(res.data)} corpus entries:")
for item in res.data:
    print(f"- [{item['source']}] {item['text']} (Student: {item['student_id']})")
