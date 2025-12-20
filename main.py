import asyncio
import json
import logging
import os
import wave
import time
import signal
import sys
import threading
import gc
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
load_dotenv()

import httpx
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

# --- ANALYZER IMPORTS ---
from AssemblyAIv2.analyzers.session_analyzer import SessionAnalyzer
from AssemblyAIv2.analyzers.pos_analyzer import POSAnalyzer
from AssemblyAIv2.analyzers.ngram_analyzer import NgramAnalyzer
from AssemblyAIv2.analyzers.verb_analyzer import VerbAnalyzer
from AssemblyAIv2.analyzers.article_analyzer import ArticleAnalyzer
from AssemblyAIv2.analyzers.amalgum_analyzer import AmalgumAnalyzer
from AssemblyAIv2.analyzers.comparative_analyzer import ComparativeAnalyzer
from AssemblyAIv2.analyzers.phenomena_matcher import ErrorPhenomenonMatcher
from AssemblyAIv2.analyzers.student_corpus_engine import StudentCorpusEngine
from AssemblyAIv2.analyzers.lm_gateway import run_lm_gateway_query
from AssemblyAIv2.ingest_audio import (
    calculate_file_hash,
    perform_batch_diarization,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SemanticServer")

# --- CONFIGURATION ---
api_key = os.getenv("ASSEMBLYAI_API_KEY")
GITENGLISH_API_BASE = os.getenv("GITENGLISH_API_BASE", "https://gitenglishhub-production.up.railway.app")
GITENGLISH_MCP_SECRET = os.getenv("MCP_SECRET")

# Global State
connected_clients = set()
main_loop = None
audio_stream_manager = None

current_session = {
    "session_id": None,
    "start_time": None,
    "student_name": "Unknown",
    "turns": [],
    "file_path": None,
    "notes": "",
    "audio_path": None 
}

# --- RESOURCE CLEANUP ---

def cleanup_resources():
    """Release all hardware and network locks."""
    logger.info("🧹 Commencing Deep Resource Cleanup...")
    
    # 1. Close Audio
    global audio_stream_manager
    if audio_stream_manager:
        try:
            audio_stream_manager.close()
            logger.info("✅ Audio stream released")
        except: pass

    # 2. Clear temp files
    try:
        temp_dir = Path("temp_repos")
        if temp_dir.exists():
            import shutil
            # shutil.rmtree(temp_dir) # Uncomment if safe
            logger.info(f"✅ Temp directory inspected: {temp_dir}")
    except: pass

    # 3. Force GC
    gc.collect()
    logger.info("✅ Memory garbage collection triggered")

def signal_handler(sig, frame):
    cleanup_resources()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit_registered = False
import atexit
if not atexit_registered:
    atexit.register(cleanup_resources)
    atexit_registered = True

# --- STUDENT HUB (PURE BEDROCK) ---

async def get_existing_students() -> list[str]:
    """Instant load from local bedrock. No network overhead."""
    students = {"System Test Student"}
    try:
        p = Path("student_profiles.json")
        if p.exists():
            with open(p, "r") as f:
                data = json.load(f)
                for s in data:
                    if s and "Tutor" not in str(s):
                        students.add(str(s))
            logger.info(f"📖 Bedrock: Loaded {len(students)} students")
    except Exception as e:
        logger.error(f"❌ Bedrock load failed: {e}")
    
    return sorted(list(students))

# --- HUB SYNC ---

async def send_to_gitenglish(action: str, student_id_or_name: str, params: dict[str, Any]) -> dict[str, Any]:
    if not GITENGLISH_MCP_SECRET:
        return {"success": False, "error": "MCP_SECRET missing"}
    
    url = f"{GITENGLISH_API_BASE}/api/mcp"
    headers = {"Authorization": f"Bearer {GITENGLISH_MCP_SECRET}", "Content-Type": "application/json"}
    payload = {"action": action, "studentId": student_id_or_name, "params": params}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json() if response.status_code == 200 else {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- WEBSOCKET HANDLER ---

async def broadcast_message(message):
    if connected_clients:
        msg = json.dumps(message)
        await asyncio.gather(*[client.send(msg) for client in connected_clients], return_exceptions=True)

async def websocket_handler(websocket):
    connected_clients.add(websocket)
    logger.info("🔌 UI Connected via WebSocket")
    try:
        # Send initial list
        students = await get_existing_students()
        payload = {"message_type": "student_list", "students": students}
        logger.info(f"📤 Sending student list to UI: {len(students)} names")
        await websocket.send(json.dumps(payload))
        
        async for message in websocket:
            data = json.loads(message)
            m_type = data.get("message_type")
            
            if m_type == "get_students":
                students = await get_existing_students()
                await websocket.send(json.dumps({"message_type": "student_list", "students": students}))
            
            elif m_type == "start_session":
                current_session["student_name"] = data.get("student_name", "Unknown")
                current_session["turns"] = []
                logger.info(f"🚀 Starting session for: {current_session['student_name']}")
                threading.Thread(target=run_streaming_client, daemon=True).start()
                
            elif m_type == "end_session":
                logger.info("🛑 Stop requested by UI")
                # Termination handled via stream close in run_streaming_client
                
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

# --- AUDIO STREAMING ---

class MonoMicrophoneStream:
    def __init__(self, device_index=7):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=16000, 
            input=True, 
            input_device_index=device_index, 
            frames_per_buffer=8000
        )
        self.audio_path = f"sessions/audio_{int(time.time())}.wav"
        os.makedirs("sessions", exist_ok=True)
        self.wf = wave.open(self.audio_path, 'wb')
        self.wf.setnchannels(1)
        self.wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        self.wf.setframerate(16000)
        current_session['audio_path'] = self.audio_path
        self.active = True

    def __iter__(self): return self
    def __next__(self):
        if not self.active: raise StopIteration
        data = self.stream.read(8000, exception_on_overflow=False)
        self.wf.writeframes(data)
        return data

    def close(self):
        self.active = False
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.wf.close()
            self.p.terminate()
        except: pass

def on_begin(self, event: BeginEvent):
    logger.info(f"✅ AssemblyAI Session Started: {event.id}")
    current_session["session_id"] = event.id
    current_session["start_time"] = datetime.now().isoformat()
    if main_loop:
        asyncio.run_coroutine_threadsafe(broadcast_message({"message_type": "session_start", "session_id": event.id}), main_loop)

def on_turn(self, event: TurnEvent):
    if not getattr(event, "end_of_turn", False):
        if main_loop:
            asyncio.run_coroutine_threadsafe(broadcast_message({"message_type": "partial", "text": event.transcript}), main_loop)
        return

    turns_list = current_session.get("turns") or []
    turn_data = {
        "turn_order": len(turns_list) + 1,
        "transcript": event.transcript,
        "speaker": "Speaker B", # Heuristic for student
        "words": [{"text": w.text, "start": w.start, "end": w.end, "confidence": w.confidence} for w in (event.words or [])],
        "timestamp": datetime.now().isoformat()
    }
    if isinstance(current_session["turns"], list):
        current_session["turns"].append(turn_data)
    else:
        current_session["turns"] = [turn_data]
    if main_loop:
        asyncio.run_coroutine_threadsafe(broadcast_message({"message_type": "transcript", **turn_data}), main_loop)

def on_error(self, error: StreamingError):
    logger.error(f"💥 AssemblyAI Error: {error}")

def run_streaming_client():
    global audio_stream_manager
    client = StreamingClient(StreamingClientOptions(api_key=api_key))
    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Error, on_error)
    
    client.connect(StreamingParameters(sample_rate=16000))
    audio_stream_manager = MonoMicrophoneStream()
    
    try:
        client.stream(audio_stream_manager)
    except Exception as e:
        logger.error(f"Stream interrupted: {e}")
    finally:
        audio_stream_manager.close()
        client.disconnect()
        logger.info("🎬 Stream Closed")

async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    logger.info("🛰️ Semantic Server starting on port 8765...")
    async with websockets.serve(websocket_handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        cleanup_resources()