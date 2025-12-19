import asyncio
import json
import logging
import os
import re
import uuid
import hashlib
import wave
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
# Load environment before any other imports that might depend on it
load_dotenv()

import httpx
from ingest_audio import perform_batch_diarization
import assemblyai as aai

# --- ANALYZER IMPORTS ---
from analyzers.session_analyzer import SessionAnalyzer
from analyzers.pos_analyzer import POSAnalyzer
from analyzers.ngram_analyzer import NgramAnalyzer
from analyzers.verb_analyzer import VerbAnalyzer
from analyzers.article_analyzer import ArticleAnalyzer
from analyzers.amalgum_analyzer import AmalgumAnalyzer
from analyzers.comparative_analyzer import ComparativeAnalyzer
from analyzers.phenomena_matcher import PhenomenaPatternMatcher
from analyzers.lemur_query import run_lemur_query
# ------------------------

from analyzers.live_feedback_agent import LiveFeedbackAgent
import numpy as np
import pyaudio
import websockets
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)
from dotenv import load_dotenv

# Optional memory monitoring
try:
    import psutil
    psutil_available = True
except ImportError:
    psutil_available = False
    psutil = None
    print("⚠️ psutil not available")

import atexit
import gc
import sys
import threading

load_dotenv()
api_key = os.getenv("ASSEMBLYAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# NO DIRECT DATABASE CONNECTIONS (Supabase/Sanity removed)
# Everything flows through the GitEnglishHub API
# -------------------------------------------------------------------------

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


def cleanup_resources():
    logger.info("Cleaning up resources...")
    try: gc.collect()
    except: pass

atexit.register(cleanup_resources)

# Load configuration
config = {}
try:
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)
except:
    config = {"app_name": "Semantic Surfer", "device_index": 7}

# WebSocket server setup
connected_clients = set()
main_loop = None

# Session storage
current_session = {
    "session_id": None,
    "start_time": None,
    "student_name": config.get("student_name", "Unknown"),
    "turns": [],
    "file_path": None,
    "notes": "",
    "audio_path": None 
}

# -------------------------------------------------------------------------
# HUB API INTEGRATION
# -------------------------------------------------------------------------
GITENGLISH_API_BASE = os.getenv("GITENGLISH_API_BASE", "https://gitenglishhub-production.up.railway.app")
GITENGLISH_MCP_SECRET = os.getenv("MCP_SECRET")

async def send_to_gitenglish(action: str, student_id_or_name: str, params: dict) -> dict:
    if not GITENGLISH_MCP_SECRET:
        logger.error("❌ MCP_SECRET not set")
        return {"success": False, "error": "MCP_SECRET missing"}
    
    url = f"{GITENGLISH_API_BASE}/api/mcp"
    headers = {"Authorization": GITENGLISH_MCP_SECRET, "Content-Type": "application/json"}
    # The Hub API handles resolving name vs ID server-side
    payload = {"action": action, "studentId": student_id_or_name, "params": params}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json() if response.status_code == 200 else {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def upload_analysis_to_hub(session_data):
    """Unified Pipeline: Local Analysis -> Hub API."""
    if not GITENGLISH_MCP_SECRET: return

    try:
        session_path = Path(session_data.get("session_file_path"))
        duration_seconds = session_data.get("duration_seconds")

        with open(session_path, 'r') as f:
            full_json = json.load(f)
        
        # 1. RUN LOCAL ANALYZERS (Using Top-Level Imports)
        main_analyzer = SessionAnalyzer(full_json)
        basic_metrics = main_analyzer.analyze_all()
        student_text = main_analyzer.student_full_text
        tutor_text = main_analyzer.teacher_full_text
        
        # Hardened Local Suite
        pos_counts = POSAnalyzer().analyze(student_text)
        pos_ratios = POSAnalyzer().get_ratios(student_text)
        ngram_data = NgramAnalyzer().analyze(student_text)
        verb_data = VerbAnalyzer().analyze(student_text)
        article_data = ArticleAnalyzer().analyze(student_text)
        
        tutor_pos_counts = POSAnalyzer().analyze(tutor_text)
        tutor_ngram = NgramAnalyzer().analyze(tutor_text)
        
        comp_data = ComparativeAnalyzer().compare(
            student_data={"pos": pos_counts, "ngrams": ngram_data, "text": student_text},
            tutor_data={"pos": tutor_pos_counts, "ngrams": tutor_ngram, "text": tutor_text}
        )
        
        detected_errors = []
        article_errs = article_data if isinstance(article_data, list) else [] # Handle list fix
        detected_errors.extend([{'error_type': 'Article Error', 'text': e['match']} for e in article_errs])
        
        verb_errs = verb_data.get('irregular_errors', [])
        detected_errors.extend([{'error_type': 'Verb Error', 'text': e['verb']} for e in verb_errs])
        
        try:
            pattern_matches = PhenomenaPatternMatcher().match(student_text)
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

        # 2. LLM Gateway Synthesis (Gemini 1.5 Pro)
        temp_session_path = session_path.parent / f"analysis_staging_{uuid.uuid4().hex}.json"
        with open(temp_session_path, 'w') as f: json.dump(full_json, f)
        analysis_results = run_lemur_query(temp_session_path, analysis_context=analysis_context)
        if temp_session_path.exists(): temp_session_path.unlink()

        lemur_data = analysis_results.get('lemur_analysis', {})
        
        # 3. Map Structured Data for Hub API
        annotated_errors = lemur_data.get('annotated_errors', [])
        extracted_phenomena = []
        for err in annotated_errors:
            extracted_phenomena.append({
                "item": err.get('quote'),
                "correction": err.get('correction'),
                "category": err.get('linguistic_category', 'Syntax'),
                "explanation": err.get('explanation'),
                "source": "LLM_ANALYSIS"
            })
            
        for err in detected_errors:
             extracted_phenomena.append({"item": err.get('text'), "category": "Grammar", "explanation": f"Detected {err.get('error_type')}", "source": "RULE_BASED"})

        student_name = full_json.get('student_name', 'Unknown')

        params = {
            'turns': [{"speaker": t.get("speaker"), "transcript": t.get("transcript", t.get("text"))} for t in full_json.get("turns", [])],
            'sessionDate': full_json.get('start_time'),
            'duration': duration_seconds,
            'lemurAnalysis': lemur_data.get('response', 'No reasoning provided.'),
            'extractedPhenomena': extracted_phenomena,
            'studentProfile': lemur_data.get('student_profile', {}),
            'notes': full_json.get('notes', ''),
            'fileHash': calculate_file_hash(str(session_path))
        }

        # FINAL SYNC: Hub resolves destination (Supabase/Sanity) server-side
        logger.info(f"📤 Handing off to Hub API for student: {student_name}")
        await send_to_gitenglish(action='ingest.createSession', student_id_or_name=student_name, params=params)

    except Exception as e:
        logger.error(f"❌ Hub handoff failed: {e}", exc_info=True)


async def run_final_cleanup_async(event):
    """Consolidated async cleanup routine."""
    logger.info("🎬 Terminating Session...")
    save_session_to_file()
    
    try:
        with open(current_session["file_path"], 'r') as f:
            session_data = json.load(f)
            
        if session_data.get("audio_path") and os.path.exists(session_data["audio_path"]):
             student_name = session_data.get("student_name", "Student")
             logger.info("👥 Running High-Definition Batch Diarization...")
             all_turns, duration = await perform_batch_diarization(session_data["audio_path"], student_name)
             if all_turns:
                 session_data["turns"] = all_turns
                 if duration: session_data["duration_seconds"] = duration
                 with open(current_session["file_path"], 'w') as f: json.dump(session_data, f, indent=2)

        session_data["session_file_path"] = current_session["file_path"]
        await upload_analysis_to_hub(session_data)
    except Exception as e:
        logger.error(f"Final cleanup sequence failed: {e}")

    if main_loop:
        await broadcast_message({"message_type": "session_end", "audio_duration_seconds": event.audio_duration_seconds})


# -------------------------------------------------------------------------
# ASSEMBLYAI EVENT HANDLERS
# -------------------------------------------------------------------------
def on_begin(self: type[StreamingClient], event: BeginEvent):
    logger.info(f"✅ SESSION STARTED: {event.id}")
    # Global current_session update
    current_session["session_id"] = event.id
    current_session["start_time"] = datetime.now().isoformat()
    
    # Path setup
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_name = current_session["student_name"].replace(" ", "_").lower()
    current_session["file_path"] = f"sessions/{safe_name}_session_{ts}.json"
    Path("sessions").mkdir(exist_ok=True)

    if main_loop:
        asyncio.run_coroutine_threadsafe(broadcast_message({"message_type": "session_start", "session_id": event.id}), main_loop)

def on_turn(self: type[StreamingClient], event: TurnEvent):
    if not getattr(event, "end_of_turn", False):
        if main_loop:
            asyncio.run_coroutine_threadsafe(broadcast_message({"message_type": "partial", "text": event.transcript}), main_loop)
        return

    # SAVE TURN LOGIC
    words_data = []
    if hasattr(event, "words") and event.words:
        for word in event.words:
            words_data.append({"text": word.text, "start_ms": word.start, "end_ms": word.end, "confidence": word.confidence})

    turn_data = {
        "turn_order": event.turn_order,
        "transcript": event.transcript,
        "speaker": f"Speaker {getattr(event, 'speaker', 'A')}",
        "words": words_data,
        "timestamp": datetime.now().isoformat()
    }
    current_session["turns"].append(turn_data)
    
    if main_loop:
        asyncio.run_coroutine_threadsafe(broadcast_message({"message_type": "transcript", **turn_data}), main_loop)

def on_terminated(self: type[StreamingClient], event: TerminationEvent):
    if main_loop:
        asyncio.run_coroutine_threadsafe(run_final_cleanup_async(event), main_loop)

def on_error(self: type[StreamingClient], error: StreamingError):
    logger.error(f"Stream Error: {error}")

# -------------------------------------------------------------------------
# AUDIO & WS HANDLERS
# -------------------------------------------------------------------------
async def websocket_handler(websocket):
    connected_clients.add(websocket)
    try:
        students = get_existing_students()
        await websocket.send(json.dumps({"message_type": "student_list", "students": students}))
        async for message in websocket:
            data = json.loads(message)
            if data.get("message_type") == "start_session":
                current_session["student_name"] = data.get("student_name", "Unknown")
                threading.Thread(target=run_streaming_client, daemon=True).start()
            elif data.get("message_type") == "update_notes":
                current_session["notes"] = data.get("notes", "")
                save_session_to_file()
            elif data.get("message_type") == "mark_update":
                # Instant visual update handled in handle_mark_update_sync
                handle_mark_update_sync(data)
    finally:
        connected_clients.remove(websocket)

def handle_mark_update_sync(data):
    turn_order = data.get("turn_order")
    text = data.get("text")
    for t in current_session["turns"]:
        if t["turn_order"] == turn_order:
            if text and "words" in t:
                for w in t["words"]:
                    if w["text"] == text: w["marked"] = True
            else:
                t["marked"] = True
    save_session_to_file()

async def broadcast_message(message):
    if connected_clients:
        msg = json.dumps(message)
        await asyncio.gather(*[client.send(msg) for client in connected_clients])

class MonoMicrophoneStream:
    def __init__(self, device_index=7):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=device_index, frames_per_buffer=8000)
        self.audio_path = f"sessions/audio_{int(time.time())}.wav"
        self.wf = wave.open(self.audio_path, 'wb')
        self.wf.setnchannels(1)
        self.wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        self.wf.setframerate(16000)
        current_session['audio_path'] = self.audio_path

    def __iter__(self): return self
    def __next__(self):
        data = self.stream.read(8000, exception_on_overflow=False)
        self.wf.writeframes(data)
        return data

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.wf.close()
        self.p.terminate()

def run_streaming_client():
    client = StreamingClient(StreamingClientOptions(api_key=api_key))
    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.connect(StreamingParameters(sample_rate=16000))
    stream = MonoMicrophoneStream(device_index=int(config.get("device_index", 7)))
    try: client.stream(stream)
    finally:
        stream.close()
        client.disconnect()

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    async with websockets.serve(websocket_handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
