import os
import json
from pathlib import Path
from pathlib import Path
import asyncio
import uuid
import logging
import hashlib
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict, cast, Any
from collections.abc import Mapping, Sequence

# Ensure workspace root is on sys.path so `import AssemblyAIv2.*` works even when running as a script.
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

# Load environment early
from dotenv import load_dotenv # type: ignore
# Load environment properly from gitenglishhub
# Load environment properly from gitenglishhub
env_path = WORKSPACE_ROOT / "gitenglishhub" / ".env.local"
if env_path.exists():
    _ = load_dotenv(dotenv_path=env_path, override=True)
else:
    _ = load_dotenv() # Fallback

import assemblyai as aai # type: ignore
import httpx # type: ignore
import asyncio
from AssemblyAIv2.analyzers.sentence_chunker import chunk_transcript
from AssemblyAIv2.analyzers.lexical_engine import LexicalEngine
from AssemblyAIv2.run_local_analysis import run_tiered_analysis

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
# Using OpenRouter for Gemini Intelligence
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

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

if not OPENROUTER_API_KEY:
    logger.warning("⚠️ OPENROUTER_API_KEY not set! AI Analysis will be skipped.")

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
    students: set[str] = set()
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

async def send_to_gitenglish(action: str, student_id_or_name: str, params: Mapping[str, object] | None = None) -> Mapping[str, object]:
    if not GITENGLISH_MCP_SECRET:
        # logger.error("❌ MCP_SECRET not set") # Removed to reduce noise if intentional
        return {"success": False, "error": "MCP_SECRET missing"}
    
    url = f"{GITENGLISH_API_BASE}/api/mcp"
    # GitEnglishHub expects: Authorization: Bearer <MCP_SECRET>
    headers = {"Authorization": f"Bearer {GITENGLISH_MCP_SECRET}", "Content-Type": "application/json"}
    payload = {"action": action, "studentId": student_id_or_name, "params": params or {}}
    
    try:
        async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json() if response.status_code == 200 else {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def purge_old_captures(base_dir: Path, retention_days: int = 7):
    """
    Purges student capture directories that are older than `retention_days`.
    This ensures local storage doesn't grow indefinitely.
    """
    if not base_dir.exists():
        return

    cutoff_time = datetime.now() - timedelta(days=retention_days)
    logger.info(f"🧹 Running retention purge on {base_dir} (Cutoff: {cutoff_time.date()})")

    # Traverse: .session_captures / student_name / date_folder
    for student_dir in base_dir.iterdir():
        if not student_dir.is_dir():
            continue
            
        for date_dir in student_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            try:
                # Parse folder name YYYY-MM-DD
                folder_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if folder_date < cutoff_time:
                    logger.info(f"🗑️ Purging old capture: {date_dir}")
                    shutil.rmtree(date_dir)
                    # If student dir is empty after purge, remove it too
                    if not any(student_dir.iterdir()):
                        student_dir.rmdir() 
            except ValueError:
                continue # Skip non-date folders

async def generate_llm_analysis(
    student_name: str, 
    transcript_text: str, 
    user_notes: str, 
    analysis_context: dict[str, Any]
):
    """
    Hands off analysis to the local Semantic Server (The Brain).
    """
    logger.info(f"🧠 Handing off analysis to Semantic Server for {student_name}...")
    
    url = "http://localhost:8080/analyze"
    payload = {
        "student_name": student_name,
        "transcript_text": transcript_text,
        "turns": [] # We pass transcript_text for now
    }
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                llm_res = result.get("llm_analysis", {})
                
                # Adapt Semantic Server response to local expected format
                return {
                    "termination": {"reason": "success"},
                    "response": llm_res.get("session_summary", "Analysis Complete"),
                    "annotated_errors": llm_res.get("language_feedback", []),
                    "student_profile": {"boss_notes": llm_res.get("boss_notes", "")},
                    "raw_output": result
                }
            else:
                logger.error(f"❌ Semantic Server Error: {response.status_code}")
                return {"error": f"Semantic Server Error {response.status_code}"}
                
    except Exception as e:
        logger.error(f"💥 Failed to reach Semantic Server: {e}")
        return {"error": str(e)}

async def perform_batch_diarization(audio_path: str, student_name: str) -> Mapping[str, object] | None:
    """
    High-Definition Batch Diarization (DUAL-PASS PROTOCOL).
    Pass 1: Get Speaker Labels (Requires Punctuation).
    Pass 2: Get Raw Text (No Punctuation).
    Merge: Align Speaker Labels to Raw Words.
    """
    logger.info(f"🎙️ Starting Dual-Pass Diarization for {audio_path}...")
    
    # --- CACHE CHECK (God-Tier Efficiency) ---
    file_hash = calculate_file_hash(audio_path)
    cache_path = WORKSPACE_ROOT / "AssemblyAIv2/ingestion_cache.json"
    cache_data: dict[str, object] = {} # type: ignore
    
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                cache_data = cast(dict[str, object], json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

    # If we have a cached result for this hash, USE IT.
    if file_hash and file_hash in cache_data:
        logger.info(f"⚡ CACHE HIT (Local)! Skipping Upload & Transcription for {file_hash[:8]}...")
        return cast(Mapping[str, object], cache_data[file_hash])

    # [NEW] Hub-Level Deduplication (Zero Waste)
    if file_hash:
        logger.info(f"🔍 Checking Hub for existing session with hash {file_hash[:8]}...")
        # We use a dummy studentId for lookup or better, an action that doesn't require it
        check_res = await send_to_gitenglish("ingest.checkHash", "system", {"fileHash": file_hash})
        if check_res.get('success') and check_res.get('data', {}).get('exists'):
            logger.info("⚡ CACHE HIT (Hub)! Reclaiming existing session data...")
            return cast(Mapping[str, object], check_res.get('data', {}).get('result'))

    transcriber = aai.Transcriber()
    
    # --- PASS 1: STRUCTURE (Diarization) ---
    logger.info("   🔹 Pass 1: Extracting Speaker Labels (Universal, Punctuation=ON, Enhanced Metadata=ON)...")
    config_diar = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.universal,
        language_code="en_us",
        speaker_labels=True,
        speakers_expected=2,
        punctuate=True,
        format_text=False,
        sentiment_analysis=True,
        entity_detection=True,
        auto_highlights=True,
        content_safety=True
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
        disfluencies=True,
        entity_detection=True
    )

    try:
        # 1. UPLOAD ONCE
        logger.info("   🔹 Uploading audio file...")
        try:
            upload_url = await asyncio.to_thread(transcriber.upload_file, audio_path)
        except Exception as e:
            logger.critical(f"💥 FATAL: Audio upload failed: {e}")
            return None

        # 2. SUBMIT BOTH JOBS
        logger.info("   🔹 Submitting Dual-Pass Transcriptions...")
        try:
            t_diar_task = asyncio.to_thread(transcriber.transcribe, upload_url, config_diar)
            t_raw_task = asyncio.to_thread(transcriber.transcribe, upload_url, config_raw)
            t_diar, t_raw = await asyncio.gather(t_diar_task, t_raw_task)
        except Exception as e:
            logger.critical(f"💥 FATAL: Transcription job submission failed: {e}")
            return None

        # --- VALIDATION ---
        if t_diar.status == aai.TranscriptStatus.error:
            logger.error(f"❌ Pass 1 (Diarization) Failed: {t_diar.error}")
            # Even if it fails, we might proceed with raw if that's better than nothing.
            # For now, we'll fail hard.
            return None
        if t_raw.status == aai.TranscriptStatus.error:
            logger.error(f"❌ Pass 2 (Raw Content) Failed: {t_raw.error}")
            return None

        logger.info("   ✅ Both passes complete. Merging...")

        # --- MERGE LOGIC ---
        # Strategy: Iterate through RAW words. Find corresponding Speaker from Diarized words based on time overlap.
        
        # Build Diarized Word Map: [(start, end, speaker)]
        diar_map: list[dict[str, float | str]] = []
        if t_diar.utterances:
            for utt in t_diar.utterances:
                for w in utt.words:
                    diar_map.append({
                        'start': w.start,
                        'end': w.end,
                        'speaker': utt.speaker or "Unknown"
                    })
        
        # Sort diar_map by start time for efficient searching (though words should be sorted already)
        diar_map.sort(key=lambda x: float(x['start']))
        
        # Build Final Turns
        # We will reconstruct turns based on SPEAKER CHANGES in the merged stream.
        
        current_speaker: str = "Unknown"
        current_words: list[RawWord] = []
        all_turns: list[SessionTurn] = []
        
        # Iterate Raw Words
        raw_words = t_raw.words if t_raw.words else [] # Use the top-level words list from Raw transcript
        
        # [REVISED] More robust speaker mapping logic
        # Helper to find speaker for a given time range
        diar_idx = 0
        for i, w in enumerate(raw_words):
            w_start, w_end = w.start, w.end
            found_speaker: str | None = None

            # Search for an overlapping speaker tag
            temp_idx = diar_idx
            while temp_idx < len(diar_map):
                d = diar_map[temp_idx]
                d_start, d_end = float(d['start']), float(d['end'])

                # Advance if diarization is behind
                if d_end < w_start:
                    diar_idx = temp_idx
                    temp_idx += 1
                    continue

                # Break if diarization is too far ahead
                if d_start > w_end:
                    break
                
                # Overlap found
                found_speaker = str(d['speaker'])
                break
            
            # --- Fallback Logic ---
            if not found_speaker:
                # If no speaker found, inherit from the previous word's speaker.
                # This handles cases where diarization might miss a word.
                if i > 0 and 'speaker' in raw_words[i-1]:
                    found_speaker = raw_words[i-1]['speaker']
                    logger.debug(f"      Word '{w.text}' inherited speaker '{found_speaker}'")
                else:
                    # For the very first word or unusual cases, default to "A"
                    found_speaker = "A"
                    logger.warning(f"      Word '{w.text}' defaulted to speaker 'A'")

            # Attach speaker to the word object itself for robust turn construction
            w.speaker = found_speaker

            # --- Turn Construction ---
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
             sentences = [{"text": s.text, "start": s.start, "end": s.end} for s in t_diar.get_sentences()] # type: ignore
        except:
             pass

        # [NEW] High-Fidelity Context Pillar: Smart Overlapping Chunks
        # This replaces naive splitting with sentence-aware overlapping windows (Context Pillar)
        smart_chunks = []
        if punctuated_text:
            try:
                smart_chunks = chunk_transcript(punctuated_text, max_chunk_chars=4000, sentence_overlap=2)
                logger.info(f"   🧩 Generated {len(smart_chunks)} smart context chunks (High-Fidelity).")
            except Exception as e:
                logger.warning(f"   ⚠️ Smart chunking failed: {e}")

        logger.info(f"✅ Dual-Pass Merge Complete. Turns: {len(all_turns)}")

        # Serialize full transcript objects for "enhanced metadata"
        # We store the raw API responses if available, or build comprehensive dicts
        
        def serialize_words(words):
            return [{"text": w.text, "start": w.start, "end": w.end, "confidence": w.confidence, "speaker": getattr(w, 'speaker', None)} for w in words]

        result = {
            "turns": all_turns,
            "duration": audio_duration,
            "punctuated_text": punctuated_text,
            "sentences": sentences,
            "smart_chunks": smart_chunks,
            # User Requested: "every instance of the v transcript cache"
            "raw_transcript_text": t_raw.text,
            "diarized_transcript_text": t_diar.text,
            "words_raw": serialize_words(t_raw.words),
            "words_diarized": serialize_words(t_diar.words),
            "raw_response_diar": t_diar.json_response,
            "raw_response_raw": t_raw.json_response
        }

        # --- CACHE WRITE ---
        if file_hash:
            try:
                # Reload cache in case of parallel writes (simple race condition handling)
                current_cache = {}
                if cache_path.exists():
                     with open(cache_path, "r") as f:
                        current_cache = json.load(f)
                
                current_cache[file_hash] = result
                
                with open(cache_path, "w") as f:
                    json.dump(current_cache, f, indent=2)
                logger.info(f"💾 Saved result to cache for {file_hash[:8]}")
            except Exception as e:
                logger.warning(f"Failed to write cache: {e}")

        return result

    except Exception as e:
        logger.error(f"❌ Dual-Pass Diarization error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def process_and_upload(audio_path: str, student_name: str, notes: str = "", transcript_id: str | None = None) -> Mapping[str, object]:
    logger.info(f"🚀 Batch Ingest: {audio_path if audio_path else 'Existing ID'} for {student_name}")
    
    diar_result = None
    if transcript_id:
        logger.info(f"🔗 Using existing Transcript ID: {transcript_id}")
        transcriber = aai.Transcriber()
        try:
            # Corrected SDK call
            t_diar = aai.Transcript.get_by_id(transcript_id)
            
            # Reconstruct turns from utterances
            all_turns = []
            if t_diar.utterances:
                for utt in t_diar.utterances:
                    all_turns.append({
                        'speaker': utt.speaker or "Unknown",
                        'transcript': utt.text,
                        'start': utt.start,
                        'end': utt.end,
                        'confidence': utt.confidence,
                        'words': [{'text': w.text, 'start': w.start, 'end': w.end, 'confidence': w.confidence, 'speaker': utt.speaker} for w in utt.words]
                    })
            
            diar_result = {
                "turns": all_turns,
                "duration": float(t_diar.audio_duration or 0.0),
                "punctuated_text": t_diar.text or "",
                "sentences": [], # sentences might not be easily fetchable without another call, keep simple
                "smart_chunks": [], # Not regenerating for legacy ID fetches to save time/complexity
                "raw_transcript_text": t_diar.text,
                "diarized_transcript_text": t_diar.text
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch existing transcript {transcript_id}: {e}")
            return {"success": False, "error": "transcript_fetch_failed"}
    else:
        # 1. Diarize via audio file
        diar_result = await perform_batch_diarization(audio_path, student_name)
    
    if not diar_result:
        logger.error("❌ Processing failed.")
        return {"success": False, "error": "diarization_failed"}

    all_turns = cast(list[SessionTurn], diar_result["turns"])
    duration = cast(float, diar_result["duration"])

    # --- SPEAKER NORMALIZATION ---
    # Ensure speakers are "A", "B", etc. to match SessionAnalyzer expectations
    unique_speakers = sorted(list(set(t['speaker'] for t in all_turns)))
    # If speakers are already single letters A, B, keep them. Otherwise remap.
    # Note: If we have "Speaker A", "Speaker B", this will remap them to A, B.
    # If we have "0", "1", it maps to A, B.
    speaker_remap = {}
    for i, s in enumerate(unique_speakers):
        # specific check if it's already a single letter to avoid A->A redundant map or A->B accidental shift if sorted wrong
        # But simple sequential remapping is usually safest if we don't trust the labels
        speaker_remap[s] = chr(65 + i) # A, B, C...

    logger.info(f"🔄 Remapping Speakers: {speaker_remap}")
    
    for t in all_turns:
        t['speaker'] = speaker_remap.get(t['speaker'], t['speaker'])
        # Also update word-level speaker labels if they exist
        if 'words' in t:
            for w in t['words']:
                if 'speaker' in w:
                     w['speaker'] = speaker_remap.get(w['speaker'], w['speaker'])

    # 2. Local Analysis (Tiered Suite)
    # Refactored to separate module per architecture guidelines
    # Passing "all 4 transcripts" (Turns, Sentences, Punctuated, Raw)
    analysis_context = run_tiered_analysis(
        student_name=student_name, 
        all_turns=cast(list[dict[str, Any]], all_turns), 
        notes=notes,
        sentences=diar_result.get("sentences"),
        punctuated_text=diar_result.get("punctuated_text"),
        raw_text=diar_result.get("raw_transcript_text")
    )

    # 3. LLM_ANALYSIS (Gemini 3 Flash Preview)
    transcript_full = "\n".join([f"{t['speaker']}: {t['transcript']}" for t in all_turns])
    llm_analysis = diar_result.get('llm_analysis')
    
    if llm_analysis:
        logger.info("⚡ LLM CACHE HIT! Reusing existing analysis...")
    else:
        logger.info("🦅 Generating LLM via AssemblyAI (Gemini 3 Flash Preview)...")
        
        llm_analysis = await generate_llm_analysis(
            student_name=student_name,
            transcript_text=transcript_full,
            user_notes=notes,
            analysis_context=analysis_context
        )
        
        # Save LLM result to cache
        file_hash = calculate_file_hash(audio_path)
        if file_hash:
            cache_path = WORKSPACE_ROOT / "AssemblyAIv2/ingestion_cache.json"
            try:
                current_cache = {}
                if cache_path.exists():
                    with open(cache_path, "r") as f:
                        current_cache = json.load(f)
                
                if file_hash in current_cache:
                    current_cache[file_hash]['llm_analysis'] = llm_analysis
                    with open(cache_path, "w") as f:
                        json.dump(current_cache, f, indent=2)
                    logger.info(f"💾 LLM Analysis cached for {file_hash[:8]}")
            except: pass

    # 4. Final Handoff to Hub API
    # ... [error_phenomena logic] ...
    
    # [NEW] SAVE TO CACHE BEFORE HANDOFF (Include AI Result)
    if diar_result and not diar_result.get('llm_analysis'):
        # Update the original diar_result with the AI analysis so the cache write at the end of diarization captures it
        # Actually, diarization happens before this. We need to manually update the cache file now.
        file_hash = calculate_file_hash(audio_path)
        if file_hash:
            cache_path = WORKSPACE_ROOT / "AssemblyAIv2/ingestion_cache.json"
            try:
                current_cache = {}
                if cache_path.exists():
                    with open(cache_path, "r") as f:
                        current_cache = json.load(f)
                
                if file_hash in current_cache:
                    current_cache[file_hash]['llm_analysis'] = llm_analysis
                    with open(cache_path, "w") as f:
                        json.dump(current_cache, f, indent=2)
                    logger.info(f"💾 AI Analysis cached for {file_hash[:8]}")
            except: pass
    error_phenomena = []
    if isinstance(llm_analysis, dict):
        annotated_errors = llm_analysis.get('annotated_errors', [])
        if isinstance(annotated_errors, list):
            for err in annotated_errors:
                if isinstance(err, dict):
                    error_phenomena.append({
                        "item": err.get('specificPhenomenon') or err.get('quote'), # Map specificPhenomenon to item
                        "correction": err.get('suggestedCorrection') or err.get('correction'),
                        "category": err.get('category', 'Syntax'),
                        "explanation": err.get('explanation'),
                        "source": f"AI_{err.get('source_weight', 'AUTO')}"
                    })
    
    # Extract detected errors from the analysis context
    detected_errors = analysis_context.get('detected_errors', [])
    for err in detected_errors:
        if isinstance(err, dict):
            error_phenomena.append({
                "item": err.get('text'), 
                "category": "Grammar", 
                "explanation": f"Detected {err.get('error_type')}", 
                "source": "RULE_BASED"
            })



    # [NEW] PERSISTENCE LAYER: Save local artifacts as requested
    # Changed to hidden directory .session_captures per user request
    captures_root = WORKSPACE_ROOT / "AssemblyAIv2/.session_captures"
    capture_dir = captures_root / student_name / datetime.now().strftime("%Y-%m-%d")
    capture_dir.mkdir(parents=True, exist_ok=True)
    
    # Run retention policy before saving new data
    try:
        purge_old_captures(captures_root, retention_days=7)
    except Exception as e:
        logger.warning(f"⚠️ Retention purge failed (non-blocking): {e}")

    session_ts = datetime.now().strftime("%H-%M-%S")
    base_filename = f"{session_ts}_{student_name}"

    # Initialize params for Hub payload (moved up for local artifact usage)
    params = {
        'localAnalysis': analysis_context,
        # Preserve the full turn shape (incl. timestamps/confidence) for downstream metrics.
        'turns': all_turns,
        'transcriptText': transcript_full,
        'punctuatedTranscript': diar_result.get("punctuated_text", ""),
        'sentences': diar_result.get("sentences", []),
        'smartChunks': diar_result.get("smart_chunks", []),
        
        # Metadata
        'sessionDate': analysis_context.get('start_time', datetime.now().isoformat()),
        'studentName': student_name,
        'tutorName': analysis_context.get('teacher_name', "Tutor"),
        'duration': duration,
        # Contract expected by GitEnglishHub action [`ingest.createSession`](gitenglishhub/lib/petty-dantic/action-registry.ts:236)
        'llmGatewayAnalysis': llm_analysis.get('response', ''),
        'llmGatewayPhenomena': error_phenomena,
        'studentProfile': llm_analysis.get('student_profile', {}),
        # Preserve the full LLM_ANALYSIS envelope for audit/debugging.
        'pettyLlmAnalysis': llm_analysis,
        'pettyLocalAnalysis': analysis_context,
        'notes': notes,
        'fileHash': calculate_file_hash(audio_path),
        # Enhanced Metadata Pass-through
        'assemblyai_raw_response': diar_result.get("raw_response_diar"),
        'assemblyai_content_response': diar_result.get("raw_response_raw")
    }

    try:
        # --- Incomplete-Proof Downloads ---
        # We now explicitly check for the presence of data and log if it's missing,
        # ensuring that a file is always created, even if empty.

        # 1. _words.json (Authoritative)
        words_data = params.get('turns', [])
        if not words_data:
            logger.warning("   ⚠️ No 'turns' data found for _words.json. File will be empty.")
        with open(capture_dir / f"{base_filename}_words.json", "w") as f:
            json.dump(words_data, f, indent=2)

        # 2. _sentences.json
        sentences_data = params.get('sentences', [])
        if not sentences_data:
            logger.warning("   ⚠️ No 'sentences' data found for _sentences.json. File will be empty.")
        with open(capture_dir / f"{base_filename}_sentences.json", "w") as f:
            json.dump(sentences_data, f, indent=2)

        # 3. _raw.txt
        raw_text_data = params.get('transcriptText', "")
        if not raw_text_data:
            logger.warning("   ⚠️ No 'transcriptText' data found for _raw.txt. File will be empty.")
        with open(capture_dir / f"{base_filename}_raw.txt", "w") as f:
            f.write(raw_text_data)

        # 4. _diarized.txt
        diarized_text_data = params.get('punctuatedTranscript', "")
        if not diarized_text_data:
            logger.warning("   ⚠️ No 'punctuatedTranscript' data found for _diarized.txt. File will be empty.")
        with open(capture_dir / f"{base_filename}_diarized.txt", "w") as f:
            f.write(diarized_text_data)

        # 5. _petty_analysis.json (Local Analysis Metrics)
        with open(capture_dir / f"{base_filename}_petty_analysis.json", "w") as f:
            json.dump(analysis_context, f, indent=2)

        # 6. _petty_llm_analysis.json (Raw LLM Response)
        with open(capture_dir / f"{base_filename}_petty_llm_analysis.json", "w") as f:
            json.dump(llm_analysis, f, indent=2)

        logger.info(f"💾 Saved local capture artifacts to {capture_dir}")
    except Exception as e:
        logger.error(f"❌ Failed to save local artifacts: {e}")


    logger.info(f"📤 Sending Payload to Hub API for student: {student_name}")
    result = await send_to_gitenglish(action='ingest.createSession', student_id_or_name=student_name, params=params)
    
    # LOG THE FULL RESULT for debugging
    logger.info(f"📡 Full Hub API Response: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        # Extract sessionId from nested data object
        api_data = cast(dict[str, Any], result.get('data', {}))
        session_id = api_data.get('sessionId') or result.get('sessionId')
        logger.info(f"🎉 Ingestion Complete! Session: {session_id}")
        return {**result, "sessionId": session_id} # Flat map for legacy compatibility in tests
    else:
        logger.error(f"❌ Ingestion failed: {result.get('error')}")

    return result

async def main():
    print("\n" + "="*60)
    print("🎧 BATCH AUDIO INGESTION TOOL")
    print("="*60)
    
    transcript_id = input("\n🔗 Existing AssemblyAI Transcript ID (Leave blank to use file): ").strip()
    
    audio_path = ""
    if not transcript_id:
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
    _ = await process_and_upload(audio_path, student_name, notes, transcript_id=transcript_id)

if __name__ == "__main__":
    try: asyncio.run(main()) # type: ignore
    except KeyboardInterrupt: pass