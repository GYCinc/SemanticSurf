import os
import sys
import json
import asyncio
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv
import assemblyai as aai
import httpx  # Added for GitEnglishHub API
from supabase import create_client, Client

# ... (imports)

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IngestAudio")

# --- Load Environment ---
load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# GitEnglishHub Integration (The proper pipeline!)
GITENGLISH_API_BASE = os.getenv("GITENGLISH_API_BASE", "https://gitenglishhub-production.up.railway.app")
MCP_SECRET = os.getenv("MCP_SECRET")

# Initialize Supabase (Global / Shared)
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase client initialized (for student lookup only)")
    except Exception as e:
        logger.warning(f"⚠️ Supabase init failed: {e} - Will use GitEnglishHub for student lookup")
else:
    logger.info("ℹ️ Supabase not configured - Using GitEnglishHub API for everything")

# --- Interactive Mode Setup (Only runs if script is executed correctly) ---
if __name__ == "__main__":
    if not AAI_API_KEY:
        logger.error("❌ ASSEMBLYAI_API_KEY not found in environment.")
        sys.exit(1)
    
    aai.settings.api_key = AAI_API_KEY

    # Check GitEnglishHub is configured
    if not MCP_SECRET:
        logger.warning("⚠️ MCP_SECRET not set! GitEnglishHub API calls will fail.")



# --- Helper Functions (Reused/Adapted from main.py) ---

async def send_to_gitenglish(action: str, student_id: str, params: dict) -> dict:
    """
    Send data to GitEnglishHub's Petty Dantic API.
    This is THE pipeline - Semantic Surfer sends raw data, GitEnglish handles all DB logic.
    """
    if not MCP_SECRET:
        logger.error("❌ MCP_SECRET not set! Cannot call GitEnglishHub API.")
        return {"success": False, "error": "MCP_SECRET not configured"}
    
    url = f"{GITENGLISH_API_BASE}/api/mcp"
    headers: dict[str, str] = {
        "Authorization": MCP_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "action": action,
        "studentId": student_id,
        "params": params
    }
    
    logger.info(f"📤 Calling GitEnglishHub: {action}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ GitEnglishHub response: {result.get('success', 'unknown')}")
                return result
            else:
                logger.error(f"❌ GitEnglishHub error ({response.status_code}): {response.text}")
                return {"success": False, "error": response.text, "status_code": response.status_code}
    except Exception as e:
        logger.error(f"❌ Failed to call GitEnglishHub: {e}")
        return {"success": False, "error": str(e)}


def get_student_id(name):
    """Find student ID by name (username or first_name) - uses Supabase for local lookup"""
    
    # RESCUE PATCH: Hardcode Jocelyn
    if name.lower() == "jocelyn":
        return "0f77a40d-cdbc-4070-b22a-3cf06098b367"

    if not supabase:
        logger.warning("Supabase not available - returning name for GitEnglishHub to resolve")
        return name  # GitEnglishHub can resolve by name
    try:
        # Try exact username match
        res = supabase.table("students").select("id").eq("username", name).execute()
        if res.data:
            return res.data[0]['id']
        
        # Try first name match
        res = supabase.table("students").select("id").eq("first_name", name).execute()
        if res.data:
            return res.data[0]['id']
            
        return name  # Let GitEnglishHub resolve
    except Exception as e:
        logger.error(f"Error finding student ID: {e}")
        return name

async def perform_batch_diarization(audio_path: str, student_name: str) -> tuple[list[dict] | None, float | None]:
    """
    Performs dual-pass diarization:
    1. Raw pass: precise timings, no punctuation.
    2. Diarized pass: speaker labels, punctuation.
    Merges them to get precise-timed, speaker-labeled words.
    """
    logger.info(f"🎙️ Starting Batch Diarization for {audio_path}...")
    
    try:
        transcriber = aai.Transcriber()
        
        # Pass 1: Raw (No Punctuation/Formatting) for strict timing
        print(f"🕵️ Pass 1: Raw Transcription...")
        
        config_raw = aai.TranscriptionConfig(
            speech_model='universal',  # Universal for raw pass
            punctuate=False,
            format_text=False
        )
        transcript_raw = transcriber.transcribe(audio_path, config_raw)
        
        if transcript_raw.status == "error":
             print(f"❌ Raw transcription failed: {transcript_raw.error}")
             return None, None
             
        # Pass 2: Diarized (With punctuation/speakers AND Speaker ID)
        print(f"👥 Pass 2: Diarization & Speaker ID...")
        
        # Configure Speaker Identification
        # "Aaron" is the tutor. We identify him and the specific Student.
        # This replaces "Speaker A/B" with actual names.
        
        config_diarized = aai.TranscriptionConfig(
            speech_model='best',  # Best model for diarization (slam-1)
            speaker_labels=True,
            speakers_expected=2,  # Tutor + student
            punctuate=True,
            format_text=False
        )
        transcript_diarized = transcriber.transcribe(audio_path, config_diarized)
        
        if transcript_diarized.status == "error":
            print(f"❌ Diarized transcription failed: {transcript_diarized.error}")
            return None, None

        # --- MERGE: Map Raw Words to Speakers ---
        print(f"🔄 Merging Raw Words with Speaker Names...")
        
        speaker_intervals = []
        for turn in transcript_diarized.utterances:
            speaker_intervals.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': turn.speaker # This will now be "Aaron" or student_name (hopefully)
            })
            
        raw_words_with_speaker = []
        for word in transcript_raw.words:
            word_speaker = 'Unknown'
            w_center = word.start + (word.end - word.start) / 2
            
            for interval in speaker_intervals:
                if interval['start'] <= w_center <= interval['end']:
                    word_speaker = interval['speaker']
                    break
            
            raw_words_with_speaker.append({
                'text': word.text, 
                'start': word.start,
                'end': word.end,
                'confidence': word.confidence,
                'speaker': word_speaker
            })
            
        # Re-group into turns
        all_turns = []
        current_turn = None
        
        for w in raw_words_with_speaker:
            if current_turn and current_turn['speaker'] == w['speaker']:
                current_turn['words'].append(w)
                current_turn['transcript'] += " " + w['text']
                current_turn['end'] = w['end']
            else:
                if current_turn:
                    all_turns.append(current_turn)
                current_turn = {
                    'speaker': w['speaker'],
                    'transcript': w['text'],
                    'start': w['start'],
                    'end': w['end'],
                    'confidence': w['confidence'],
                    'words': [w]
                }
        if current_turn:
            all_turns.append(current_turn)

        print(f"✅ Diarization and Merge Complete. Duration: {transcript_diarized.audio_duration}s")
        return all_turns, transcript_diarized.audio_duration

    except Exception as e:
        logger.error(f"❌ Diarization error: {e}")
        return None, None

async def process_and_upload(audio_path, student_name, notes=""):
    logger.info(f"🚀 Processing: {audio_path} for {student_name}")
    
    # 1. Validate Student
    student_id = get_student_id(student_name)
    if not student_id:
        logger.error(f"❌ Student '{student_name}' not found in Supabase.")
        return
    logger.info(f"✅ Found Student ID: {student_id}")

    # 2. Diarize (Dual-Pass with Speaker ID)
    all_turns, duration = await perform_batch_diarization(audio_path, student_name)
    if all_turns is None or duration is None:
        logger.error("❌ Diarization failed or returned no data.")
        return

    # 3. Construct Session Data
    # Speakers are ALREADY mapped by AssemblyAI now!
    
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    logger.info(f"✅ Diarization Complete. Duration: {duration}s")
    
    turns = []
    # No filter here, we want ALL turns for the transcript view
    
    for turn in all_turns:
        # Construct turn object (using dict access for 'turn')
        turn_obj = {
            "speaker": turn['speaker'], # Already "Aaron" or Name
            "transcript": turn['transcript'],
            "start": turn['start'],
            "end": turn['end'],
            "confidence": turn['confidence'],
            "words": [{"text": w['text'], "start": w['start'], "end": w['end'], "confidence": w['confidence']} for w in turn['words']]
        }
        turns.append(turn_obj)

    # Note: LEmur and Corpus analysis loop later filters for speaker != "Aaron" to find student turns.

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
                    headers={"Authorization": str(AAI_API_KEY or "")},
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

    # ============================================================
    # STEP 2.5: LeMUR LINGUISTIC ANALYSIS (The "Guru")
    # ============================================================
    logger.info("🦁 Sending transcript to LeMUR for Deep Linguistic Analysis...")

    lemur_analysis = None
    extracted_phenomena = []
    prioritized_to_do_list = []
    student_profile = {}

    try:
        # Construct the "Agent Prompt" (User-Provided)
        system_prompt = """You are an expert applied linguist and instructional designer. The user will provide a transcript of a one-on-one English tutoring session between a tutor (named "Aaron") and a student. Your task is to analyze the student's spoken language, identify systematic errors (especially those that appear fossilized), and produce a personalized, prioritized to-do list to help the student improve.

## Instructions

1. **Identify the student's lines**  
   - The tutor is always labeled "Aaron". All other speech belongs to the student. Ignore the tutor's utterances for error analysis (they may be used only for context).

2. **Extract and categorize errors**  
   - Read each student utterance carefully.  
   - For each error, determine whether it is a **systematic error** (repeated, pattern‑based) or a **slip** (one‑off mistake). Focus on systematic errors; ignore slips unless they are frequent.  
   - Categorize each systematic error as one of:  
     - **Syntax** – includes word order, clause structure, and morphological issues (verb tense, aspect, agreement, articles, plurals, etc.)  
     - **Lexis** – word choice, collocations, idioms, preposition use  
     - **Pragmatics** – register, politeness, cultural appropriateness, conversational strategies  
   - Note the exact utterance, a corrected version, the category, and a brief linguistic explanation (e.g., L1 interference, overgeneralization).

3. **Estimate the student's CEFR level**  
   - Based on the overall complexity, range, and accuracy of the language, assign a CEFR level (A1, A2, B1, B2, C1, C2). Provide a short justification in your reasoning.

4. **Select the top three errors**  
   - Evaluate the impact of each systematic error on communication. Consider frequency, comprehensibility, and potential for misunderstanding.  
   - Choose **up to three** errors that are most detrimental. If there are fewer than three systematic errors, select all of them.

5. **Design specific remedial tasks**  
   - For each selected error, create **one concrete, actionable task** the student can do to address that error.  
   - Tasks must be specific (e.g., "Complete 10 gap‑fill exercises on the present perfect vs. simple past", "Use flashcards to practice collocations with 'make' and 'do'", "Record yourself making polite requests and compare with native speaker examples").  
   - Avoid vague advice like "study grammar" or "watch movies".

6. **Assign priorities**  
   - Assign each task a priority based on how urgently it should be addressed:  
     - **HIGH** – the error severely impedes understanding; address immediately.  
     - **MEDIUM** – the error is noticeable but less critical; address after high‑priority items.  
     - **LOW** – the error is minor or stylistic; address once higher priorities are handled.  
   - Use only the labels "HIGH", "MEDIUM", or "LOW" for the `priority` field.

7. **Prepare the final JSON output**  
   - Construct a JSON object **exactly** following the schema below.  
   - Do not include any extra text, commentary, or markdown formatting outside the JSON.  
   - Ensure the JSON is valid (use double quotes, escape characters properly).  
   - The JSON must contain exactly the fields described; do not add extra keys.

## Output Schema

```json
{
  "student_profile": {
    "cefr_estimate": "CEFR level (e.g., B1)",
    "dominant_issue": "A concise description of the most prominent systematic error pattern"
  },
  "internal_reasoning": "A short paragraph explaining your analysis: why you chose these errors, how you estimated the CEFR level, and any other relevant observations.",
  "annotated_errors": [
    {
      "quote": "The exact student utterance containing the error",
      "correction": "A native‑like version of the utterance",
      "linguistic_category": "Syntax / Lexis / Pragmatics",
      "explanation": "Brief linguistic description (e.g., 'L1 transfer causing omission of articles')"
    }
  ],
  "prioritized_to_do_list": [
    {
      "priority": "HIGH",
      "task": "Specific, actionable task description",
      "reason": "Explanation of how this task addresses the corresponding error"
    }
  ]
}
```
"""
        
        # Format transcript for LLM Gateway
        full_transcript_text = "\n".join([f"{t['speaker']}: {t['transcript']}" for t in turns])
        
        # --- LLM Gateway (replaces deprecated LeMUR SDK) ---
        llm_gateway_url = "https://llm-gateway.assemblyai.com/v1/chat/completions"
        llm_payload = {
            "model": "claude-sonnet-4-5-20250929",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please analyze the following transcript:\n\n{full_transcript_text}"}
            ],
            "max_tokens": 8000
        }
        llm_headers = {
            "Authorization": AAI_API_KEY,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            llm_response = await client.post(llm_gateway_url, json=llm_payload, headers=llm_headers, timeout=120.0)
        
        llm_response.raise_for_status()
        llm_result = llm_response.json()
        llm_content = llm_result.get("choices", [{}])[0].get("message", {}).get("content", "")
        llm_usage = llm_result.get("usage", {})
        
        logger.info(f"🦁 LLM Gateway Response received. Tokens: {llm_usage}")
        
        # Parse JSON
        try:
            # Clean potential markdown fences
            clean_response = llm_content.replace("```json", "").replace("```", "").strip()
            lemur_data = json.loads(clean_response)
            
            # Extract Components
            student_profile = lemur_data.get('student_profile', {})
            lemur_analysis = lemur_data.get('internal_reasoning')
            prioritized_to_do_list = lemur_data.get('prioritized_to_do_list', [])
            
            # Convert LeMUR errors to our ExtractedPhenomena format
            for err in lemur_data.get('annotated_errors', []):
                extracted_phenomena.append({
                    "item": err.get('quote'),
                    "category": err.get('linguistic_category'), 
                    "context": f"{err.get('quote')} -> {err.get('correction')}",
                    "explanation": err.get('explanation'),
                    "correction": err.get('correction'),
                    "confidence": 0.9 
                })
                
            logger.info(f"✅ Extracted {len(extracted_phenomena)} linguistic phenomena")
            logger.info(f"✅ Generated {len(prioritized_to_do_list)} remedial tasks")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM JSON response: {e}")
            logger.error(f"   Response preview: {llm_content[:500]}...")
            lemur_analysis = llm_content # Fallback to raw text

    except Exception as e:
        logger.error(f"❌ LeMUR Task Failed: {e}")

    # Build the transcript text for the analysis report (Legacy format)
    student_turns = [t for t in turns if t["speaker"] != "Aaron"]
    transcript_text = "\n".join([
        f"{t['speaker']}: {t['transcript']}"
        for t in turns
    ])
    
    # Calculate basic metrics
    total_words = sum(len(t.get('words', [])) for t in student_turns)
    
    # Build analysis report
    analysis_report = f"""Session Analysis
Duration: {duration}s
Student Words: {total_words}
Turns: {len(student_turns)}

-- LeMUR Summary --
{lemur_analysis if lemur_analysis else 'No analysis available.'}

-- Teaching Notes Analysis --
{notes_analysis.get('llm_analysis', '') if notes_analysis else ''}
"""

    # ============================================================
    # STEP 1: CREATE SESSION IN GITENGLISHHUB (For Curation UI)
    # This creates the student_sessions record so teacher can curate
    # ============================================================
    logger.info("📤 Creating session via Petty Dantic API...")
    
    session_result = await send_to_gitenglish(
        action='ingest.createSession',
        student_id=student_id,
        params={
            'turns': turns,  # Full turns data with words
            'transcriptText': transcript_text,
            'sessionDate': timestamp,
            'duration': duration,
            'lemurAnalysis': lemur_analysis,
            'extractedPhenomena': extracted_phenomena,
            'studentProfile': student_profile,
            'prioritizedToDoList': prioritized_to_do_list
        }
    )
    
    if session_result.get('success'):
        session_id = session_result.get('sessionId')
        logger.info(f"✅ Session created: {session_id}")
    else:
        logger.error(f"❌ Session creation failed: {session_result.get('error')}")
        logger.error("   Check MCP_SECRET matches between systems")
        return


    logger.info("🎉 Ingestion Complete! (Session staged for Inbox approval)")



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
