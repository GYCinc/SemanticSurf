import json
import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials missing.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_session(file_path, supabase):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return False

    session_id = data.get("session_id")
    if not session_id:
        logger.warning(f"No session_id in {file_path}, skipping.")
        return False

    # Check if session exists in Supabase
    try:
        # Check if any rows exist for this session_id
        # Using count to be efficient
        response = supabase.table("transcripts").select("id", count="exact").eq("session_id", session_id).limit(1).execute()
        if response.count > 0:
            logger.info(f"Session {session_id} already exists in Supabase. Skipping.")
            return True # Already synced
    except Exception as e:
        logger.error(f"Failed to check session existence for {session_id}: {e}")
        return False

    # Prepare rows for insertion
    turns = data.get("turns", [])
    if not turns:
        logger.warning(f"No turns in {file_path}, skipping.")
        return True # Nothing to sync

    rows = []
    for turn in turns:
        # Extract timestamp: prefer 'created', fallback to 'timestamp' (if exists), else now (bad)
        # In main.py, 'created' is saved.
        timestamp = turn.get("created")
        if not timestamp:
             # Fallback: try to construct from session start? 
             # For now, let's leave it null or let DB handle default if allowed, 
             # but DB default is 'now()'.
             # Let's use session start time if available, or just current time but that's misleading.
             timestamp = data.get("start_time") 
        
        # Ensure we have confidence (float)
        confidence = turn.get("end_of_turn_confidence")
        if confidence is None:
             # Try to calc from words
             words = turn.get("words", [])
             if words:
                 confidence = sum(w.get("confidence", 1.0) for w in words) / len(words)
             else:
                 confidence = 1.0 # Default

        row = {
            "session_id": session_id,
            "speaker": turn.get("speaker", "Unknown"),
            "text": turn.get("transcript", ""),
            "turn_order": turn.get("turn_order", 0),
            "confidence": confidence,
            "timestamp": timestamp,
            "metadata": {
                "words": turn.get("words"),
                "pauses": turn.get("pauses"),
                "analysis": turn.get("analysis")
            }
        }
        rows.append(row)

    # Batch insert
    batch_size = 100
    total_inserted = 0
    
    try:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            supabase.table("transcripts").insert(batch).execute()
            total_inserted += len(batch)
        
        logger.info(f"✅ Synced {total_inserted} turns for session {session_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to insert rows for {session_id}: {e}")
        return False

def main():
    supabase = get_supabase_client()
    if not supabase:
        return

    session_files = sorted(glob.glob("sessions/*.json"))
    logger.info(f"Found {len(session_files)} local session files.")

    if not session_files:
        return

    for file_path in tqdm(session_files, desc="Syncing Sessions"):
        sync_session(file_path, supabase)

if __name__ == "__main__":
    main()

