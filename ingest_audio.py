import os
import sys
import json
import asyncio
import logging
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import assemblyai as aai
from supabase import create_client, Client

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IngestAudio")

# --- Load Environment ---
load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

if not AAI_API_KEY:
    logger.error("❌ ASSEMBLYAI_API_KEY not found in environment.")
    sys.exit(1)

aai.settings.api_key = AAI_API_KEY

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase: {e}")
        sys.exit(1)
else:
    logger.error("❌ Supabase credentials missing.")
    sys.exit(1)

# --- Helper Functions (Reused/Adapted from main.py) ---

def get_student_id(name):
    """Find student ID by name (username or first_name)"""
    try:
        # Try exact username match
        res = supabase.table("students").select("id").eq("username", name).execute()
        if res.data:
            return res.data[0]['id']
        
        # Try first name match
        res = supabase.table("students").select("id").eq("first_name", name).execute()
        if res.data:
            return res.data[0]['id']
            
        return None
    except Exception as e:
        logger.error(f"Error finding student ID: {e}")
        return None

async def perform_batch_diarization(audio_path):
    """
    Uploads audio to AssemblyAI Batch API for accurate diarization.
    Returns the transcript object.
    """
    if not os.path.exists(audio_path):
        logger.error(f"❌ Audio file not found: {audio_path}")
        return None

    logger.info("🔄 Starting Batch Diarization...")
    try:
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            speakers_expected=2, # Tutor + Student
            punctuate=True,
            format_text=True
        )
        
        # Using synchronous transcribe to avoid Python 3.12 Future await error
        transcript = transcriber.transcribe(audio_path, config)
        
        if transcript.status == "error":
            logger.error(f"❌ Diarization failed: {transcript.error}")
            return None
            
        return transcript

    except Exception as e:
        logger.error(f"❌ Diarization error: {e}")
        return None

async def process_and_upload(audio_path, student_name, notes=""):
    logger.info(f"🚀 Processing: {audio_path} for {student_name}")
    
    # 1. Validate Student
    student_id = get_student_id(student_name)
    if not student_id:
        logger.error(f"❌ Student '{student_name}' not found in Supabase.")
        return
    logger.info(f"✅ Found Student ID: {student_id}")

    # 2. Diarize
    transcript = await perform_batch_diarization(audio_path)
    if not transcript:
        return

    # 3. Construct Session Data
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    duration = transcript.audio_duration
    
    logger.info(f"✅ Diarization Complete. Duration: {duration}s")
    
    # Map speakers (Simple heuristic: Speaker A = Aaron, B = Student)
    speaker_map = {
        "A": "Aaron",
        "B": student_name
    }
    
    turns = []
    for utt in transcript.utterances:
        speaker_label = utt.speaker
        speaker_name = speaker_map.get(speaker_label, speaker_label)
        
        turns.append({
            "speaker": speaker_name,
            "transcript": utt.text,
            "start": utt.start,
            "end": utt.end,
            "confidence": utt.confidence,
            "words": [{"text": w.text, "start": w.start, "end": w.end, "confidence": w.confidence} for w in utt.words]
        })

    # 4. Analyze Notes (LLM)
    import httpx
    notes_analysis = None
    if notes:
        logger.info("📝 Analyzing notes with LLM...")
        try:
            prompt = f"""Analyze these tutor notes from an ESL class session. Extract:
1. Key teaching moments or observations
2. Action items for the tutor (things to look up, send, prepare)
3. Student progress indicators
4. Areas of concern

Notes: {notes}

Provide a structured JSON response with: teaching_moments, action_items, progress_notes, concerns"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://llm-gateway.assemblyai.com/v1/chat/completions",
                    headers={"Authorization": AAI_API_KEY},
                    json={
                        "model": "anthropic/claude-3-5-sonnet",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    notes_analysis = {
                        "raw_notes": notes,
                        "llm_analysis": result['choices'][0]['message']['content']
                    }
                    logger.info("✅ Notes analyzed successfully")
        except Exception as e:
            logger.warning(f"Note analysis failed: {e}")
            notes_analysis = {"raw_notes": notes}

    # 5. Upload to Supabase (student_sessions)
    session_data = {
        "student_id": student_id,
        "session_date": timestamp,
        "duration_seconds": int(duration) if duration else 0,
        # "transcript_json": {"turns": turns}, # Column missing in schema 
        # "summary": "Manual Ingestion", # Column missing in schema
        "metrics": {
            "wpm": 0, 
            "filler_words": 0,
            "notes": notes_analysis
        }
    }
    
    try:
        res = supabase.table("student_sessions").insert(session_data).execute()
        logger.info(f"✅ Session uploaded to Supabase: {res.data[0]['id']}")
    except Exception as e:
        logger.error(f"❌ Failed to upload session: {e}")
        return

    # 5. Upload to Corpus (student_corpus)
    logger.info("📚 Building corpus...")
    corpus_entries = []
    for i, turn in enumerate(turns):
        if turn["speaker"] != "Aaron": # Only student turns
            entry = {
                "student_id": student_id,
                "text": turn["transcript"],
                "source": "transcript",
                "metadata": {
                    "session_id": session_id,
                    "turn_order": i,
                    "confidence": turn["confidence"]
                }
            }
            corpus_entries.append(entry)
    
    if corpus_entries:
        try:
            supabase.table("student_corpus").insert(corpus_entries).execute()
            logger.info(f"✅ Added {len(corpus_entries)} turn entries to student corpus")
        except Exception as e:
            logger.error(f"❌ Failed to upload corpus: {e}")

    # 6. Upload Word-Level Corpus
    logger.info("📖 Building word-level corpus...")
    word_corpus_entries = []
    for i, turn in enumerate(turns):
        if turn["speaker"] != "Aaron": # Only student turns
            for word in turn.get("words", []):
                word_entry = {
                    "student_id": student_id,
                    "text": word.get("text", ""),
                    "source": "word",
                    "metadata": {
                        "session_id": session_id,
                        "turn_order": i,
                        "word_start_ms": word.get("start"),
                        "word_end_ms": word.get("end"),
                        "confidence": word.get("confidence")
                    }
                }
                word_corpus_entries.append(word_entry)
    
    if word_corpus_entries:
        try:
            # Insert in batches to avoid rate limits
            batch_size = 100
            for i in range(0, len(word_corpus_entries), batch_size):
                batch = word_corpus_entries[i:i + batch_size]
                supabase.table("student_corpus").insert(batch).execute()
            logger.info(f"✅ Added {len(word_corpus_entries)} individual words to corpus")
        except Exception as e:
            logger.error(f"❌ Failed to upload word corpus: {e}")

    # 6. Run LeMUR Analysis (8 Categories)
    logger.info("🤖 Running LeMUR Classification (8 Categories)...")
    try:
        from analyzers.lemur_query import run_lemur_query
        
        # Save temp session file for LeMUR to read
        temp_session_path = Path(f"sessions/temp_{session_id}.json")
        temp_session_data = {
            "session_id": session_id,
            "student_name": student_name,
            "speaker_map": speaker_map,
            "turns": turns
        }
        with open(temp_session_path, 'w') as f:
            json.dump(temp_session_data, f)
            
        classification_prompt = (
            "Analyze the student's speech based ONLY on the text transcript. Do NOT hallucinate audio features like pronunciation or flow. "
            "1. **Topics & Subjects**: List the main topics discussed (e.g., 'Travel', 'Business Meetings').\n"
            "2. **Linguistic Analysis**: Rate (1-10) and comment on these 6 text-based categories:\n"
            "   - Grammar (Syntax, tense usage)\n"
            "   - Vocabulary (Word choice, range)\n"
            "   - Phrasal Verbs (Usage of multi-word verbs)\n"
            "   - Expressions (Idiomatic usage)\n"
            "   - Discourse (Coherence, sentence structure)\n"
            "   - Sociolinguistics (Register, politeness, tone)\n"
            "Format the output as a structured JSON-like list."
        )
        
        analysis_results = run_lemur_query(temp_session_path, custom_prompt=classification_prompt)
        
        # Clean up temp file
        if temp_session_path.exists():
            temp_session_path.unlink()
            
        # 7. Upload Report to Sanity (via API)
        import httpx
        
        sanity_project_id = os.getenv("SANITY_PROJECT_ID")
        sanity_dataset = os.getenv("SANITY_DATASET", "production")
        sanity_token = os.getenv("SANITY_API_TOKEN") or os.getenv("SANITY_API_KEY")
        
        if sanity_project_id and sanity_token:
            logger.info("📤 Uploading Report to Sanity...")
            url = f"https://{sanity_project_id}.api.sanity.io/v2021-06-07/data/mutate/{sanity_dataset}"
            headers = {
                "Authorization": f"Bearer {sanity_token}",
                "Content-Type": "application/json"
            }
            
            # Create a simple document
            lemur_response = analysis_results.get('lemur_analysis', {}).get('response', 'No analysis generated.')
            
            mutations = {
                "mutations": [
                    {
                        "create": {
                            "_type": "lessonAnalysis", # Generic type
                            "studentName": student_name,
                            "sessionDate": timestamp,
                            "analysisReport": lemur_response,
                            "scores": {} # Placeholder for parsed scores if needed
                        }
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=mutations)
                
            if res.status_code == 200:
                logger.info(f"✅ Sanity Upload Success: {res.json()}")
            else:
                logger.error(f"❌ Sanity Upload Failed: {res.text}")
        else:
            logger.warning("⚠️ Sanity credentials missing. Skipping upload.")

    except Exception as e:
        logger.error(f"❌ Analysis/Sanity Error: {e}")

    logger.info("🎉 Ingestion Complete!")

# --- Main Interactive Loop ---
async def main():
    print("\n" + "="*60)
    print("🎧 AUDIO INGESTION TOOL")
    print("="*60)
    
    # Get Audio File
    while True:
        audio_path = input("\n📁 Drag & Drop Audio File (or type path): ").strip().replace("'", "").replace('"', "")
        if os.path.exists(audio_path):
            break
        print("❌ File not found. Try again.")

    # Get Student
    print("\n🎓 Select Student:")
    # Fetch students
    try:
        res = supabase.table("students").select("username, first_name").execute()
        students = [s.get('username') for s in res.data]
        for i, name in enumerate(students):
            print(f"  [{i+1}] {name}")
    except:
        students = []
    
    student_choice = input(f"\nEnter number or name: ").strip()
    student_name = None
    
    if student_choice.isdigit():
        idx = int(student_choice) - 1
        if 0 <= idx < len(students):
            student_name = students[idx]
    
    if not student_name:
        student_name = student_choice # Fallback to raw input

    if not student_name:
        print("❌ Invalid student.")
        return

    # Get Notes
    print("\n📝 Tutor Notes (Optional):")
    notes = input("Enter notes (or press Enter to skip): ").strip()

    await process_and_upload(audio_path, student_name, notes)

if __name__ == "__main__":
    asyncio.run(main())
