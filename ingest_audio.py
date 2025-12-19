import os
import sys
import json
import asyncio
import uuid
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, cast

# Load environment early
from dotenv import load_dotenv
_ = load_dotenv()

import assemblyai as aai
import httpx

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IngestAudio")

# --- Configuration ---
AAI_API_KEY: str = os.getenv("AAI_API_KEY", os.getenv("ASSEMBLYAI_API_KEY", ""))
GITENGLISH_API_BASE: str = os.getenv("GITENGLISH_API_BASE", "https://gitenglishhub-production.up.railway.app")
GITENGLISH_MCP_SECRET: str = os.getenv("MCP_SECRET")

# --- NO DIRECT DATABASE CONNECTIONS ---
# Everything flows through the GitEnglishHub API

# Initial Configuration
if AAI_API_KEY:
    try:
        aai.settings.api_key = AAI_API_KEY
        logger.info("✅ AssemblyAI API Key configured")
    except Exception as e:
        logger.warning(f"⚠️ AssemblyAI config failed: {e}")

if not GITENGLISH_MCP_SECRET:
    logger.warning("⚠️ GITENGLISH_MCP_SECRET not set! Hub API calls will fail.")

# --- TypedDict Definitions ---

class RawWord(TypedDict):
    text: str
    start: int
    end: int
    confidence: float
    speaker: str

class SessionTurn(TypedDict):
    speaker: str
    transcript: str
    start: int
    end: int
    confidence: float
    words: list[RawWord]

# --- Helper Functions ---

def calculate_file_hash(file_path):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing {file_path}: {e}")
        return None

def get_existing_students():
    """Load students from local cache (student_profiles.json)."""
    students = set()
    try:
        if os.path.exists("student_profiles.json"):
            with open("student_profiles.json", "r") as f:
                local_data = json.load(f)
                if isinstance(local_data, list):
                    for item in local_data:
                        if item: students.add(item)
    except Exception as e:
        logger.error(f"Failed to load local student cache: {e}")

    systemic_filters = {"Test", "Unknown", "null", None, "Tutor", "Aaron (Tutor)", "Speaker"}
    cleaned = {s for s in students if s and s not in systemic_filters and not s.startswith("Session_")}
    return sorted(list(cleaned))

async def send_to_gitenglish(action: str, student_id_or_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if not GITENGLISH_MCP_SECRET:
        logger.error("❌ MCP_SECRET not set")
        return {"success": False, "error": "MCP_SECRET missing"}
    
    url = f"{GITENGLISH_API_BASE}/api/mcp"
    headers = {"Authorization": GITENGLISH_MCP_SECRET, "Content-Type": "application/json"}
    payload = {"action": action, "studentId": student_id_or_name, "params": params or {}}
    
    try:
        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json() if response.status_code == 200 else {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def perform_batch_diarization(audio_path: str, student_name: str) -> tuple[list[SessionTurn] | None, float | None]:
    """
    High-Definition Batch Diarization.
    """
    logger.info(f"🎙️ Starting Diarization for {audio_path}...")
    
    try:
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            speaker_labels=True,
            speakers_expected=2,
            punctuate=True,
            format_text=True
        )
        
        # This is a blocking SDK call, we run it in executor for safety if needed
        # but for simple batch script we just await the wrapper
        transcript = await asyncio.to_thread(transcriber.transcribe, audio_path, config)
        
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"❌ Transcription failed: {transcript.error}")
            return None, None

        all_turns: list[SessionTurn] = []
        if transcript.utterances:
            for utt in transcript.utterances:
                turn_words: list[RawWord] = []
                if utt.words:
                    for w in utt.words:
                        turn_words.append({
                            'text': str(w.text),
                            'start': int(w.start),
                            'end': int(w.end),
                            'confidence': float(w.confidence),
                            'speaker': str(utt.speaker)
                        })
                
                all_turns.append({
                    'speaker': str(utt.speaker),
                    'transcript': str(utt.text),
                    'start': int(utt.start),
                    'end': int(utt.end),
                    'confidence': float(utt.confidence or 0.0),
                    'words': turn_words
                })
        
        audio_duration = float(transcript.audio_duration or 0.0)
        logger.info(f"✅ Diarization Complete. Turns: {len(all_turns)}, Duration: {audio_duration}s")
        return all_turns, audio_duration

    except Exception as e:
        logger.error(f"❌ Diarization error: {e}")
        return None, None

async def process_and_upload(audio_path: str, student_name: str, notes: str = ""):
    logger.info(f"🚀 Batch Ingest: {audio_path} for {student_name}")
    
    # 1. Diarize
    all_turns, duration = await perform_batch_diarization(audio_path, student_name)
    if all_turns is None or duration is None:
        logger.error("❌ Processing failed.")
        return

    # 2. Local Analysis (Tiered Suite)
    from analyzers.session_analyzer import SessionAnalyzer
    from analyzers.pos_analyzer import POSAnalyzer
    from analyzers.ngram_analyzer import NgramAnalyzer
    from analyzers.verb_analyzer import VerbAnalyzer
    from analyzers.article_analyzer import ArticleAnalyzer
    from analyzers.amalgum_analyzer import AmalgumAnalyzer
    from analyzers.comparative_analyzer import ComparativeAnalyzer
    from analyzers.phenomena_matcher import PhenomenaPatternMatcher

    # Construct unified JSON for analyzers
    session_json = {
        "session_id": str(uuid.uuid4()),
        "student_name": student_name,
        "teacher_name": "Aaron",
        "speaker_map": {"A": "Aaron", "B": student_name}, # Heuristic
        "start_time": datetime.now().isoformat(),
        "turns": all_turns,
        "notes": notes
    }

    main_analyzer = SessionAnalyzer(session_json)
    basic_metrics = main_analyzer.analyze_all()
    student_text = main_analyzer.student_full_text
    tutor_text = main_analyzer.teacher_full_text
    
    logger.info("🧠 Running Tiered Analysis Suite...")
    pos_counts = POSAnalyzer().analyze(student_text)
    pos_ratios = POSAnalyzer().get_ratios(student_text)
    ngram_data = NgramAnalyzer().analyze(student_text)
    verb_data = VerbAnalyzer().analyze(student_text)
    article_data = ArticleAnalyzer().analyze(student_text)
    
    comp_data = ComparativeAnalyzer().compare(
        student_data={"pos": pos_counts, "ngrams": ngram_data, "text": student_text},
        tutor_data={"pos": POSAnalyzer().analyze(tutor_text), "ngrams": NgramAnalyzer().analyze(tutor_text), "text": tutor_text}
    )
    
    detected_errors = []
    # Standardize Article Errors (List)
    if isinstance(article_data, list):
        detected_errors.extend([{'error_type': 'Article Error', 'text': e['match']} for e in article_data])
    
    # Standardize Verb Errors
    verb_errs = verb_data.get('irregular_errors', [])
    detected_errors.extend([{'error_type': 'Verb Error', 'text': e['verb']} for e in verb_errs])
    
    # Pattern Matching
    try:
        pattern_matches = PhenomenaPatternMatcher().match(student_text)
        for m in pattern_matches:
            detected_errors.append({'error_type': f"Pattern: {m.get('category')}", 'text': m.get('item')})
    except:
        pass

    analysis_context = {
        "caf_metrics": basic_metrics.get('caf_metrics') or "DATA_MISSING",
        "comparison": comp_data,
        "register_analysis": {"scores": AmalgumAnalyzer().analyze_register(student_text), "classification": AmalgumAnalyzer().get_genre_classification(student_text)},
        "detected_errors": detected_errors,
        "pos_summary": pos_ratios
    }

    # 3. LLM Gateway Synthesis (Claude 4.5 for Batch)
    from analyzers.lemur_query import run_lemur_query
    # Create temp file for lemur_query
    temp_path = Path(f"batch_staging_{uuid.uuid4().hex}.json")
    with open(temp_path, 'w') as f: json.dump(session_json, f)
    
    # Run analysis (Note: lemur_query is currently set to gemini-1.5-pro, 
    # but we can override model here if we want maximum depth)
    analysis_results = run_lemur_query(temp_path, analysis_context=analysis_context)
    if temp_path.exists(): temp_path.unlink()

    lemur_data = analysis_results.get('lemur_analysis', {})
    
    # 4. Final Handoff to Hub API
    extracted_phenomena = []
    for err in lemur_data.get('annotated_errors', []):
        extracted_phenomena.append({
            "item": err.get('quote'),
            "correction": err.get('correction'),
            "category": err.get('linguistic_category', 'Syntax'),
            "explanation": err.get('explanation'),
            "source": "LLM_ANALYSIS"
        })
    for err in detected_errors:
         extracted_phenomena.append({"item": err.get('text'), "category": "Grammar", "explanation": f"Detected {err.get('error_type')}", "source": "RULE_BASED"})

    params = {
        'turns': [{"speaker": t.get("speaker"), "transcript": t.get("transcript")} for t in all_turns],
        'transcriptText': "\n".join([f"{t['speaker']}: {t['transcript']}" for t in all_turns]),
        'sessionDate': session_json['start_time'],
        'duration': duration,
        'lemurAnalysis': lemur_data.get('response', 'No reasoning provided.'),
        'extractedPhenomena': extracted_phenomena,
        'studentProfile': lemur_data.get('student_profile', {}),
        'notes': notes,
        'fileHash': calculate_file_hash(audio_path)
    }

    logger.info(f"📤 Sending Payload to Hub API for student: {student_name}")
    result = await send_to_gitenglish(action='ingest.createSession', student_id_or_name=student_name, params=params)
    
    if result.get('success'):
        logger.info(f"🎉 Ingestion Complete! Session: {result.get('sessionId')}")
    else:
        logger.error(f"❌ Ingestion failed: {result.get('error')}")

async def main():
    print("\n" + "="*60)
    print("🎧 BATCH AUDIO INGESTION TOOL")
    print("="*60)
    
    audio_path = input("\n📁 Audio File Path: ").strip().replace("'", "").replace('"', "")
    if not os.path.exists(audio_path):
        print("❌ File not found.")
        return

    students = get_existing_students()
    print("\n🎓 Select Student:")
    for i, name in enumerate(students):
        print(f"  [{i+1}] {name}")
    
    choice = input(f"\nEnter number or name: ").strip()
    student_name = students[int(choice)-1] if choice.isdigit() and 0 < int(choice) <= len(students) else choice

    if not student_name:
        print("❌ Invalid student.")
        return

    notes = input("\n📝 Session Notes (Optional): ").strip()
    await process_and_upload(audio_path, student_name, notes)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass