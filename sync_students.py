import os
import json
import certifi
# FORCE SSL CERT FILE for macOS
os.environ['SSL_CERT_FILE'] = certifi.where()

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ Missing credentials")
else:
    try:
        supabase = create_client(url, key)
        res = supabase.table("students").select("username, first_name").execute()
        
        if res.data:
            local_profiles = []
            for s in res.data:
                # Use first_name as the display name if available, otherwise username
                display_name = s.get('first_name') or s.get('username')
                local_profiles.append(display_name)
            
            # Update student_profiles.json
            with open("student_profiles.json", "w") as f:
                json.dump(local_profiles, f, indent=2)
                
            print(f"✅ Synced {len(local_profiles)} students from Cloud to Local.")
        else:
            print(" (No students found in Cloud)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
