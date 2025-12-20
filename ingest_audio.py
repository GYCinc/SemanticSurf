import os
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
GITENGLISH_API_BASE: str = os.getenv("GITENGLISH_API_BASE", "https://gitenglish.com")
GITENGLISH_MCP_SECRET: str = os.getenv("MCP_SECRET", "")

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

def calculate_file_hash(file_path: str | Path) -> str | None:
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing {file_path}: {e}")
        return None

def get_existing_students() -> list[str]:
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

async def perform_batch_diarization(audio_path: str, student_name: str) -> dict[str, Any] | None:
    """
    High-Definition Batch Diarization (DUAL-PASS PROTOCOL).
    Pass 1: Get Speaker Labels (Requires Punctuation).
    Pass 2: Get Raw Text (No Punctuation).
    Merge: Align Speaker Labels to Raw Words.
    """
    logger.info(f"🎙️ Starting Dual-Pass Diarization for {audio_path}...")
    transcriber = aai.Transcriber()
    
    # --- PASS 1: STRUCTURE (Diarization) ---
    logger.info("   🔹 Pass 1: Extracting Speaker Labels (Universal, Punctuation=ON)...")
    config_diar = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.universal,
        language_code="en_us",
        speaker_labels=True,
        speakers_expected=2,
        punctuate=True,
        format_text=True # Need True for full readability
    )
    
    # --- PASS 2: CONTENT (Raw Reality) ---
    logger.info("   🔹 Pass 2: Extracting Raw Content (Universal, Punctuation=OFF)...")
    config_raw = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.universal,
        language_code="en_us",
        speaker_labels=False,
        speakers_expected=2,
        punctuate=False,
        format_text=False,
        disfluencies=True
    )

    try:
        # 1. UPLOAD ONCE
        logger.info("   🔹 Uploading audio file...")
        upload_url = await asyncio.to_thread(transcriber.upload_file, audio_path)
        
        # 2. SUBMIT BOTH JOBS
        logger.info("   🔹 Submitting Dual-Pass Transcriptions...")
        t_diar_task = asyncio.to_thread(transcriber.transcribe, upload_url, config_diar)
        t_raw_task = asyncio.to_thread(transcriber.transcribe, upload_url, config_raw)
        
        t_diar, t_raw = await asyncio.gather(t_diar_task, t_raw_task)
        
        if t_diar.status == aai.TranscriptStatus.error:
            logger.error(f"❌ Pass 1 Failed: {t_diar.error}")
            return None
        if t_raw.status == aai.TranscriptStatus.error:
            logger.error(f"❌ Pass 2 Failed: {t_raw.error}")
            return None

        logger.info("   ✅ Both passes complete. Merging...")

        # --- MERGE LOGIC ---
        # Strategy: Iterate through RAW words. Find corresponding Speaker from Diarized words based on time overlap.
        
        # Build Diarized Word Map: [(start, end, speaker)]
        diar_map = []
        if t_diar.utterances:
            for utt in t_diar.utterances:
                for w in utt.words:
                    diar_map.append({
                        'start': w.start,
                        'end': w.end,
                        'speaker': utt.speaker
                    })
        
        # Sort diar_map by start time for efficient searching (though words should be sorted already)
        diar_map.sort(key=lambda x: x['start'])
        
        # Build Final Turns
        # We will reconstruct turns based on SPEAKER CHANGES in the merged stream.
        
        current_speaker = "Unknown"
        current_words: list[RawWord] = []
        all_turns: list[SessionTurn] = []
        
        # Iterate Raw Words
        raw_words = t_raw.words if t_raw.words else [] # Use the top-level words list from Raw transcript
        
        # Helper to find speaker for a given time range
        # Simple optimization: keep track of last index
        diar_idx = 0
        
        for w in raw_words:
            w_start = w.start
            w_end = w.end
            found_speaker = None
            
            # Look ahead in diar_map
            # We look for ANY overlap.
            temp_idx = diar_idx
            while temp_idx < len(diar_map):
                d = diar_map[temp_idx]
                if d['end'] < w_start:
                    # Diarized word ended before this raw word started. Move pointer.
                    diar_idx = temp_idx # Safe to advance
                    temp_idx += 1
                    continue
                
                if d['start'] > w_end:
                    # Diarized word starts after this raw word ends. No overlap possible anymore.
                    break
                
                # Overlap found!
                found_speaker = d['speaker']
                break # Take first overlap
            
            if not found_speaker:
                # Fallback: Inherit previous speaker or Unknown
                found_speaker = current_speaker if current_speaker != "Unknown" else "A" 
            
            # Start new turn if speaker changed
            if found_speaker != current_speaker:
                if current_words:
                    # Flush previous turn
                    all_turns.append({
                        'speaker': current_speaker,
                        'transcript': " ".join([cw['text'] for cw in current_words]),
                        'start': current_words[0]['start'],
                        'end': current_words[-1]['end'],
                        'confidence': sum(cw['confidence'] for cw in current_words) / len(current_words),
                        'words': current_words
                    })
                current_speaker = found_speaker
                current_words = []
            
            # Add to current buffer
            current_words.append({
                'text': w.text,
                'start': w.start,
                'end': w.end,
                'confidence': w.confidence,
                'speaker': current_speaker
            })
            
        # Flush final turn
        if current_words:
            all_turns.append({
                'speaker': current_speaker,
                'transcript': " ".join([cw['text'] for cw in current_words]),
                'start': current_words[0]['start'],
                'end': current_words[-1]['end'],
                'confidence': sum(cw['confidence'] for cw in current_words) / len(current_words),
                'words': current_words
            })

        audio_duration = float(t_raw.audio_duration or 0.0)

        # Extract Rich Data from Pass 1
        punctuated_text = t_diar.text or ""
        sentences = []
        try:
             # Try to get sentences if available
             sentences = [{"text": s.text, "start": s.start, "end": s.end} for s in t_diar.get_sentences()]
        except:
             # Fallback if get_sentences() fails or isn't available
             pass

        logger.info(f"✅ Dual-Pass Merge Complete. Turns: {len(all_turns)}")

        return {
            "turns": all_turns,
            "duration": audio_duration,
            "punctuated_text": punctuated_text,
            "sentences": sentences
        }

    except Exception as e:
        logger.error(f"❌ Dual-Pass Diarization error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def process_and_upload(audio_path: str, student_name: str, notes: str = ""):
    logger.info(f"🚀 Batch Ingest: {audio_path} for {student_name}")
    
    # 1. Diarize
    diar_result = await perform_batch_diarization(audio_path, student_name)
    if not diar_result:
        logger.error("❌ Processing failed.")
        return

    all_turns = diar_result["turns"]
    duration = diar_result["duration"]

    # 2. Local Analysis (Tiered Suite)
    from analyzers.session_analyzer import SessionAnalyzer
    from analyzers.pos_analyzer import POSAnalyzer
    from analyzers.ngram_analyzer import NgramAnalyzer
    from analyzers.verb_analyzer import VerbAnalyzer
    from analyzers.article_analyzer import ArticleAnalyzer
    from analyzers.amalgum_analyzer import AmalgumAnalyzer
    from analyzers.comparative_analyzer import ComparativeAnalyzer
    from analyzers.phenomena_matcher import ErrorPhenomenonMatcher
    from analyzers.preposition_analyzer import PrepositionAnalyzer
    from analyzers.learner_error_analyzer import LearnerErrorAnalyzer
        
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

    main_analyzer = SessionAnalyzer(cast(dict[str, object], session_json))
    basic_metrics = main_analyzer.analyze_all()
    student_text = main_analyzer.student_full_text
    tutor_text = main_analyzer.teacher_full_text
    
    logger.info("🧠 Running Tiered Analysis Suite...")
    pos_counts = POSAnalyzer().analyze(student_text)
    pos_ratios = POSAnalyzer().get_ratios(student_text)
    ngram_data = NgramAnalyzer().analyze(student_text)
    verb_data = VerbAnalyzer().analyze(student_text)
    article_data = ArticleAnalyzer().analyze(student_text)
    prep_data = PrepositionAnalyzer().analyze(student_text)
    learner_data = LearnerErrorAnalyzer().analyze(student_text)
    
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

    # Standardize Preposition Errors
    detected_errors.extend([{'error_type': 'Preposition Error', 'text': e['item']} for e in prep_data])

    # Standardize Learner Errors (PELIC)
    detected_errors.extend([{'error_type': f"Learner: {e.get('category')}", 'text': e['item']} for e in learner_data])
    
    # Pattern Matching
    try:
        pattern_matches = ErrorPhenomenonMatcher().match(student_text)
        for m in pattern_matches:
            detected_errors.append({'error_type': f"Pattern: {m.get('category')}", 'text': m.get('item')})
    except: pass

    analysis_context = {
        "caf_metrics": basic_metrics.get('caf_metrics') or "DATA_MISSING",
        "comparison": comp_data,
        "register_analysis": {"scores": AmalgumAnalyzer().analyze_register(student_text), "classification": AmalgumAnalyzer().get_genre_classification(student_text)},
        "detected_errors": detected_errors,
        "pos_summary": pos_ratios
    }

    # 3. LLM Gateway Synthesis (Claude 4.5 for Batch)
    from analyzers.llm_gateway import run_lm_gateway_query
    # Create temp file for lemur_query
    temp_path = Path(f"batch_staging_{uuid.uuid4().hex}.json")
    with open(str(temp_path), 'w') as f: json.dump(session_json, f)
            
    # Run analysis (Note: lm_gateway is currently set to gemini-1.5-pro, 
    # but we can override model here if we want maximum depth)
    from analyzers.schemas import Turn
    turn_objs: list[Turn] = []
    for i, t in enumerate(all_turns or []):
        turn_objs.append(Turn(
            turn_order=i + 1,
            transcript=t['transcript'],
            speaker=t['speaker'],
            timestamp=datetime.fromtimestamp(t['start'] / 1000).isoformat() if t.get('start') else datetime.now().isoformat()
        ))

    analysis_results = run_lm_gateway_query(
        student_name=student_name,
        turns=turn_objs,
        analysis_context=analysis_context,
        session_id=str(session_json.get("session_id", "")),
        notes=notes
    )
    if temp_path.exists(): temp_path.unlink()

    if isinstance(analysis_results, dict):
        gateway_data = analysis_results.get('lm_analysis', {})
    else:
        gateway_data = {}

    # 4. Final Handoff to Hub API
    error_phenomena = []
    if isinstance(gateway_data, dict):
        annotated_errors = gateway_data.get('annotated_errors', [])
        if isinstance(annotated_errors, list):
            for err in annotated_errors:
                if isinstance(err, dict):
                    error_phenomena.append({
                        "item": err.get('quote'),
                        "correction": err.get('correction'),
                        "category": err.get('linguistic_category', 'Syntax'),
                        "explanation": err.get('explanation'),
                        "source": "LLM_ANALYSIS"
                    })
    
    for err in detected_errors:
        if isinstance(err, dict):
            error_phenomena.append({
                "item": err.get('text'), 
                "category": "Grammar", 
                "explanation": f"Detected {err.get('error_type')}", 
                "source": "RULE_BASED"
            })

    params = {
        'turns': [{"speaker": t.get("speaker"), "transcript": t.get("transcript"), "words": t.get("words")} for t in all_turns if isinstance(t, dict)],
        'transcriptText': "\n".join([f"{t['speaker']}: {t['transcript']}" for t in all_turns if isinstance(t, dict)]),
        'punctuatedTranscript': diar_result.get("punctuated_text", ""),
        'sentences': diar_result.get("sentences", []),
        'sessionDate': session_json['start_time'],
        'duration': duration,
        'lmAnalysis': gateway_data.get('response', 'No reasoning provided.') if isinstance(gateway_data, dict) else 'No reasoning provided.',
        'errorPhenomena': error_phenomena,
        'studentProfile': gateway_data.get('student_profile', {}) if isinstance(gateway_data, dict) else {},
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