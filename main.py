import asyncio
import json
import logging
import os
import re
import hashlib # Added for duplicate prevention
import wave # Added by user
import time # Added by user
from datetime import datetime
from pathlib import Path
from typing import Type

import httpx # Added for LLM Gateway
from assemblyai import Transcriber, TranscriptionConfig  # FIX: Added missing imports
import assemblyai as aai
from analyzers.material_agent import MaterialAgent
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
    StreamingSessionParameters,
    TerminationEvent,
    TurnEvent,
)
from dotenv import load_dotenv

# Optional memory monitoring
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available - memory monitoring disabled")

import atexit
import gc
import sys
import threading
import time

load_dotenv()
api_key = os.getenv("ASSEMBLYAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"API Key loaded: {'Yes' if api_key else 'No'}")

# -------------------------------------------------------------------------
# SUPABASE SETUP
# -------------------------------------------------------------------------
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = object  # Mock class to avoid NameError
    print("⚠️ supabase package not installed. Run: pip install supabase")

# Initialize Supabase Client
supabase: Client = None
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if SUPABASE_AVAILABLE and supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase client: {e}")
else:
    logger.warning("⚠️ Supabase credentials missing or package not installed. Cloud streaming disabled.")


def stream_to_supabase_sync(turn_data: dict, session_id: str):
    """Push a single transcript turn to Supabase (fire and forget)"""
    if not supabase:
        return
    # DISABLED: transcripts table not in current schema
    # Data is saved to student_corpus at session end instead
    return
    # try:
    #     row = {
    #         "session_id": session_id,
    #         "speaker": turn_data.get("speaker"),
    #         "text": turn_data.get("transcript"),
    #         "turn_order": turn_data.get("turn_order"),
    #         "confidence": turn_data.get("end_of_turn_confidence"),
    #         "timestamp": turn_data.get("created") or datetime.now().isoformat(),
    #         "metadata": {
    #             "words": turn_data.get("words"),
    #             "pauses": turn_data.get("pauses"),
    #             "analysis": turn_data.get("analysis")
    #         }
    #     }
    #     supabase.table("transcripts").insert(row).execute()
    # except Exception as e:
    #     logger.error(f"Supabase Sync Error: {e}")


# -------------------------------------------------------------------------
# MEMORY MANAGEMENT (Restored)
# -------------------------------------------------------------------------
def monitor_memory():
    """Monitor memory usage and shutdown if threshold exceeded"""
    if not PSUTIL_AVAILABLE:
        logger.warning("⚠️ psutil not available - memory monitoring disabled")
        return

    while True:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            if memory_info.rss > 1024 * 1024 * 1024 * 4:  # 4GB threshold
                logger.warning("⚠️ Memory usage exceeded 4GB. Shutting down...")
                sys.exit(1)
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Memory monitoring error: {e}")
            break


def cleanup_resources():
    """Cleanup resources on exit"""
    logger.info("Cleaning up resources...")
    try:
        gc.collect()
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
    logger.info("Resources cleaned up")


# Register cleanup on exit
atexit.register(cleanup_resources)


# -------------------------------------------------------------------------
# AUDIO DEVICE VALIDATION (Restored)
# -------------------------------------------------------------------------
def validate_audio_device(device_index):
    """Validate audio device exists and has input channels - FAIL LOUDLY if not"""
    p = pyaudio.PyAudio()
    try:
        device_count = p.get_device_count()

        if device_index >= device_count or device_index < 0:
            print("\n" + "=" * 70)
            print("❌ AUDIO DEVICE ERROR")
            print("=" * 70)
            print(f"Device index {device_index} does not exist!")
            print(f"\n📋 Available input devices:")
            print(f"{'Index':<8} {'Name':<45} {'Channels':<10}")
            print("-" * 70)

            for i in range(device_count):
                info = p.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    marker = " ← RECOMMENDED" if "Aggregate" in info["name"] else ""
                    print(
                        f"{i:<8} {info['name']:<45} {info['maxInputChannels']:<10}{marker}"
                    )

            print("\n💡 Fix: Update config.json with a valid device_index")
            print("=" * 70 + "\n")
            return False

        device_info = p.get_device_info_by_index(device_index)
        if device_info["maxInputChannels"] == 0:
            print("\n" + "=" * 70)
            print("❌ AUDIO DEVICE ERROR")
            print("=" * 70)
            print(
                f"Device {device_index} ({device_info['name']}) has NO input channels!"
            )
            print(f"\n📋 Available input devices:")
            print(f"{'Index':<8} {'Name':<45} {'Channels':<10}")
            print("-" * 70)

            for i in range(device_count):
                info = p.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0:
                    marker = " ← RECOMMENDED" if "Aggregate" in info["name"] else ""
                    print(
                        f"{i:<8} {info['name']:<45} {info['maxInputChannels']:<10}{marker}"
                    )

            print("\n💡 Fix: Update config.json with a valid input device")
            print("=" * 70 + "\n")
            return False

        print(
            f"✅ Audio device validated: [{device_index}] {device_info['name']} ({device_info['maxInputChannels']} channels)"
        )
        return True

    finally:
        p.terminate()


# Load configuration
config = {}
try:
    with open("config.json", "r") as f:
        config = json.load(f)
    logger.info(f"Config loaded: Speaker={config.get('speaker_name', 'Unknown')}")
except Exception as e:
    logger.warning(f"Could not load config.json: {e}")
    config = {"speaker_name": "Speaker", "app_name": "Semantic Surfer"}

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
    "audio_path": None  # New: Path to saved WAV file
}


# -------------------------------------------------------------------------
# LLM ANALYSIS (AssemblyAI Gateway)
# -------------------------------------------------------------------------
# Initialize MaterialAgent
material_agent = MaterialAgent(api_key=api_key)

async def analyze_turn_with_llm(text, context=""):
    """Analyze a student turn using the MaterialAgent"""
    return await material_agent.analyze_turn(text, context)


# -------------------------------------------------------------------------
# SESSION MANAGEMENT
# -------------------------------------------------------------------------
def normalize_student_name(name):
    """Normalize student names to prevent duplicates"""
    if not name:
        return "Unknown"
    # Remove extra spaces, standardize case, remove parenthetical descriptions
    normalized = name.strip().lower()
    # Remove common parenthetical descriptions like "(Tutor)"
    normalized = re.sub(r'\s*\([^)]*\)\s*$', '', normalized)
    # Capitalize first letter of each word
    return ' '.join(word.capitalize() for word in normalized.split())

def calculate_file_hash(file_path):
    """Calculate MD5 hash of a file for duplicate detection"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None

def get_existing_students():
    """Scan Supabase students table for active student names - with proper deduplication"""
    if not supabase:
        logger.warning("⚠️ Supabase not connected. Falling back to local file scan.")
        return get_local_existing_students()

    try:
        # Query the actual students table from GitEnglish Hub
        response = supabase.table("students").select("first_name, username").execute()
        
        students = set()
        if response.data:
            for row in response.data:
                # Skip Aaron entries
                username = row.get("username", "")
                first_name = row.get("first_name", "")
                if "Aaron" in str(username) or "Aaron" in str(first_name):
                    continue
                    
                # ONLY use username (descriptive format), ignore first_name to prevent duplicates
                # Convert username like "david-saves-snacks-2025" to "David Saves Snacks 2025"
                if username:
                    # Convert kebab-case to readable: "david-saves-snacks-2025" -> "David Saves Snacks 2025"
                    display_name = ' '.join(word.capitalize() for word in username.split('-'))
                    students.add(display_name)
                # Don't add first_name - this prevents "David" and "David Saves Snacks 2025" both appearing
        
        # Also merge with local session files to catch any not in Supabase yet
        local_students = get_local_existing_students()
        students.update(local_students)
        
        # Filter out invalid/generic names
        invalid_names = {"Unknown", "Speaker", "Student", "Test", "Aaron", "Tutor"}
        valid_students = {s for s in students if s and s not in invalid_names and not s.startswith("Session_")}
        
        return sorted(list(valid_students))
        
    except Exception as e:
        logger.error(f"Error fetching students from Supabase: {e}")
        return get_local_existing_students()

def get_local_existing_students():
    """Scan sessions directory for unique student names (Fallback)"""
    students = set()
    try:
        if not os.path.exists("sessions"):
            return []
        
        # Glob the files
        files = Path("sessions").glob("*.json")
        for f in files:
            try:
                data = json.loads(f.read_text())
                if "student_name" in data:
                    students.add(data["student_name"])
            except:
                continue
                
    except Exception as e:
        logger.error(f"Error reading sessions: {e}")
    
    return sorted(list(students))


def start_new_session(session_id, student_name=None):
    """Initialize a new session with local storage"""
    global current_session

    # If no student name provided, use config default or fallback
    if not student_name:
        student_name = config.get("student_name") or config.get("speaker_name", "Speaker")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    Path("sessions").mkdir(exist_ok=True)

    # Sanitize student name for filename
    safe_student_name = student_name.replace(" ", "_").lower()
    
    # Filename: {StudentName}_session_{Timestamp}.json
    # The AssemblyAI Session ID is stored INSIDE the JSON, keeping the filename readable.
    if safe_student_name and safe_student_name not in ["unknown", "speaker"]:
        filename = f"sessions/{safe_student_name}_session_{timestamp}.json"
    else:
        filename = f"sessions/session_{timestamp}.json"

    current_session = {
        "session_id": session_id,  # UUID stored here for reference
        "start_time": datetime.now().isoformat(),
        "student_name": student_name, 
        "turns": [],
        "file_path": filename,
        "audio_path": None # Will be set by MonoMicrophoneStream
    }

    logger.info(f"New session started: {session_id} for student: {student_name}")
    logger.info(f"Saving to: {current_session['file_path']}")


def save_turn_to_session(event: TurnEvent):
    """Save complete turn data with all metadata"""

    words_data = []
    pauses = []

    if hasattr(event, "words") and event.words:
        for i, word in enumerate(event.words):
            word_data = {
                "text": word.text,
                "start_ms": word.start,
                "end_ms": word.end,
                "duration_ms": word.end - word.start,
                "confidence": word.confidence,
                "word_is_final": word.word_is_final,
            }
            words_data.append(word_data)

            if i < len(event.words) - 1:
                next_word = event.words[i + 1]
                pause_duration = next_word.start - word.end
                if pause_duration > 0:
                    pauses.append(
                        {
                            "after_word_index": i,
                            "after_word": word.text,
                            "before_word": next_word.text,
                            "duration_ms": pause_duration,
                        }
                    )

    speaking_rate = None
    turn_duration_ms = None

    if words_data and len(words_data) > 0:
        turn_duration_ms = words_data[-1]["end_ms"] - words_data[0]["start_ms"]
        # --- WPM FILTER FIX: Only calculate WPM for turns with 4 or more words ---
        if turn_duration_ms > 0 and len(words_data) >= 4:
            speaking_rate = (len(words_data) / turn_duration_ms) * 60000

    detected_speaker = getattr(event, "speaker", "A") # Default to 'A' if None
    
    # Map speakers: 'A' -> 'Aaron', 'B' -> Student Name
    final_speaker_name = detected_speaker
    if detected_speaker == "A":
        final_speaker_name = config.get("speaker_name", "Aaron")
    elif detected_speaker == "B":
        final_speaker_name = current_session.get("student_name", "Student")

    turn_data = {
        "turn_order": event.turn_order,
        "transcript": event.transcript,
        "speaker": final_speaker_name,
        "turn_is_formatted": event.turn_is_formatted,
        "end_of_turn": event.end_of_turn,
        "end_of_turn_confidence": event.end_of_turn_confidence,
        "created": event.created.isoformat() if hasattr(event, "created") else None,
        "words": words_data,
        "pauses": pauses,
        "analysis": {
            "word_count": len(words_data),
            "turn_duration_ms": turn_duration_ms,
            "speaking_rate_wpm": round(speaking_rate, 2) if speaking_rate else None,
            "total_pause_time_ms": sum(p["duration_ms"] for p in pauses),
            "pause_count": len(pauses),
            "avg_pause_duration_ms": round(
                sum(p["duration_ms"] for p in pauses) / len(pauses), 2
            )
            if pauses
            else 0,
            "avg_word_confidence": round(
                sum(w["confidence"] for w in words_data) / len(words_data), 4
            )
            if words_data
            else None,
            "low_confidence_words": [
                w["text"] for w in words_data if w["confidence"] < 0.7
            ],
        },
    }

    existing_turn = next(
        (t for t in current_session["turns"] if t["turn_order"] == event.turn_order),
        None,
    )

    if existing_turn:
        existing_turn.update(turn_data)
    else:
        current_session["turns"].append(turn_data)


def save_session_to_file():
    """Write current session to JSON file (optimized for speed)"""
    if not current_session["file_path"]:
        return

    session_data = {
        "app_name": config.get("app_name", "Semantic Surfer"),
        "session_id": current_session["session_id"],
        "speaker": config.get("speaker_name", "Speaker"),
        "student_name": current_session.get("student_name", "Unknown"), # Include student name in saved file
        "start_time": current_session["start_time"],
        "end_time": datetime.now().isoformat(),
        "total_turns": len(current_session["turns"]),
        "total_words": sum(len(turn["words"]) for turn in current_session["turns"]),
        "turns": current_session["turns"],
        "audio_path": current_session["audio_path"] # Include audio path
    }

    try:
        with open(current_session["file_path"], "w") as f:
            json.dump(session_data, f)
        gc.collect()
    except Exception as e:
        logger.error(f"Failed to save session: {e}")


# -------------------------------------------------------------------------
# WEBSOCKET HANDLER
# -------------------------------------------------------------------------
async def websocket_handler(websocket):
    connected_clients.add(websocket)
    logger.info(f"Client connected. Total clients: {len(connected_clients)}")
    
    # --- Send Existing Students List on Connect ---
    try:
        students = get_existing_students()
        await websocket.send(json.dumps({
            "message_type": "student_list",
            "students": students
        }))
    except Exception as e:
        logger.error(f"Failed to send student list: {e}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("message_type") == "mark_update":
                    # --- CRASH FIX: Use correct asyncio executor loop ---
                    loop = asyncio.get_event_loop()
                    loop.run_in_executor(None, handle_mark_update_sync, data)
                elif data.get("message_type") == "update_notes":
                    # Save notes from viewer
                    notes = data.get("notes", "")
                    current_session["notes"] = notes
                    save_session_to_file()
                    logger.info("📝 Notes updated")
                elif data.get("message_type") == "update_profile":
                    # Handle profile updates from frontend
                    student_name = data.get("student_name")
                    if student_name:
                        logger.info(f"Updating profile to: {student_name}")
                        
                        # Update session metadata
                        current_session["student_name"] = student_name
                        
                        # Update filename to match new student name (so it's not stuck as 'unknown')
                        try:
                            timestamp_str = current_session["start_time"]
                            # Handle potential ISO format variations or just use current time if parsing fails
                            # Actually start_time is isoformat string.
                            ts = datetime.fromisoformat(timestamp_str)
                            ts_formatted = ts.strftime("%Y-%m-%d_%H-%M-%S")
                            
                            safe_name = student_name.replace(" ", "_").lower()
                            new_filename = f"sessions/{safe_name}_session_{ts_formatted}.json"
                            current_session["file_path"] = new_filename
                            logger.info(f"Updated session filename to: {new_filename}")
                        except Exception as e:
                            logger.error(f"Error updating filename: {e}")

                        # --- Broadcast updated list ---
                        students = get_existing_students()
                        if student_name not in students:
                            students.append(student_name)
                            students.sort()
                        
                        await broadcast_message({
                            "message_type": "student_list",
                            "students": students
                        })
                
                elif data.get("message_type") == "analyze_turn":
                    # Handle analysis request from frontend
                    text = data.get("text")
                    turn_id = data.get("turn_id")
                
                elif data.get("message_type") == "start_session":
                    # Start the streaming client after student selection
                    student_name = data.get("student_name", "Unknown")
                    logger.info(f"Starting session for student: {student_name}")
                    current_session["student_name"] = student_name
                    threading.Thread(target=run_streaming_client, daemon=True).start()
                    logger.info("Streaming client started in background thread")
                
                elif data.get("message_type") == "export_session":
                    format_type = data.get("format", "json")
                    logger.info(f"Exporting session as {format_type}...")
                    
                    if not current_session["file_path"]:
                        logger.error("No session file to export")
                        continue
                        
                    try:
                        # Ensure session is saved first
                        save_session_to_file()
                        
                        export_path = current_session["file_path"]
                        content = ""
                        
                        if format_type == "markdown":
                            export_path = current_session["file_path"].replace(".json", ".md")
                            with open(current_session["file_path"], 'r') as f:
                                s_data = json.load(f)
                            
                            content = f"# Session with {s_data.get('student_name')}\n"
                            content += f"Date: {s_data.get('start_time')}\n\n"
                            content += "## Notes\n"
                            content += f"{s_data.get('notes', '')}\n\n"
                            content += "## Transcript\n"
                            for turn in s_data.get('turns', []):
                                speaker = turn.get('speaker', 'Unknown')
                                text = turn.get('transcript', '')
                                content += f"**{speaker}:** {text}\n\n"
                                
                            with open(export_path, 'w') as f:
                                f.write(content)
                                
                        elif format_type == "txt":
                            export_path = current_session["file_path"].replace(".json", ".txt")
                            with open(current_session["file_path"], 'r') as f:
                                s_data = json.load(f)
                            
                            content = f"Session: {s_data.get('student_name')} - {s_data.get('start_time')}\n"
                            content += "-" * 40 + "\n\n"
                            for turn in s_data.get('turns', []):
                                speaker = turn.get('speaker', 'Unknown')
                                text = turn.get('transcript', '')
                                content += f"{speaker}: {text}\n"
                                
                            with open(export_path, 'w') as f:
                                f.write(content)
                        
                        logger.info(f"✅ Exported to: {export_path}")
                        
                        # Notify frontend
                        await broadcast_message({
                            "message_type": "export_complete",
                            "path": export_path,
                            "format": format_type
                        })
                        
                    except Exception as e:
                        logger.error(f"Export failed: {e}")
                
                elif data.get("message_type") == "analyze_turn":
                    # Handle analysis request from frontend
                    text = data.get("text")
                    turn_id = data.get("turn_id")
                    
                    # Get some context (last 5 turns) with SPEAKER LABELS
                    context = ""
                    if current_session["turns"]:
                        recent = current_session["turns"][-5:]
                        # Map speakers: 'A' -> 'Aaron', 'B' -> Student (from config or 'Student')
                        tutor_label = config.get("speaker_name", "Aaron")
                        student_label = current_session.get("student_name", "Student")
                        
                        for t in recent:
                            spk = t.get('speaker')
                            # If speaker is still 'A' or 'B' from raw stream, map it:
                            if spk == 'A': spk_mapped = tutor_label
                            elif spk == 'B': spk_mapped = student_label
                            else: spk_mapped = spk
                            
                            context += f"{spk_mapped}: {t.get('transcript')}\n"
                    
                    logger.info(f"🔍 Analyzing turn: {text[:30]}...")
                    analysis_result = await analyze_turn_with_llm(text, context)
                    
                    # Send back to specific client or broadcast? 
                    # Ideally just the requester, but broadcast is easier for now and keeps sync
                    await websocket.send(json.dumps({
                        "message_type": "analysis_result",
                        "turn_id": turn_id,
                        "result": analysis_result
                    }))

                elif data.get("message_type") == "end_session":
                    logger.info("🛑 Session ended by user.")
                    # In a real app, we would signal the streaming thread to stop.
                    # For now, we just log it and maybe save the session one last time.
                    save_session_to_file()
                    await broadcast_message({"message_type": "session_ended"})

                elif data.get("message_type") == "archive_session":
                    logger.info("📦 Archive request received.")
                    # Placeholder for archive logic
                    save_session_to_file()
                    await websocket.send(json.dumps({
                        "message_type": "notification",
                        "text": "Session archived successfully (Simulated)"
                    }))

                elif data.get("message_type") == "get_system_health":
                    logger.info("🏥 Health check requested.")
                    health_data = {
                        "cpu_percent": 0,
                        "memory_usage": 0
                    }
                    if PSUTIL_AVAILABLE:
                        health_data["cpu_percent"] = psutil.cpu_percent()
                        health_data["memory_usage"] = psutil.virtual_memory().percent
                    
                    await websocket.send(json.dumps({
                        "message_type": "system_health",
                        "data": health_data
                    }))

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client: {message}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")
        gc.collect()


def handle_mark_update_sync(data):
    """Handle mark updates from viewer (synchronous, fast)"""
    turn_order = data.get("turn_order")
    mark_type = data.get("mark_type")

    try:
        turn = next(
            (t for t in current_session["turns"] if t["turn_order"] == turn_order), None
        )

        if turn:
            if mark_type:
                turn["marked"] = True
                turn["mark_type"] = mark_type
                turn["mark_timestamp"] = data.get("timestamp")
                logger.info(f"✓ Turn {turn_order} marked as {mark_type}")
            else:
                turn["marked"] = False
                turn["mark_type"] = None
                logger.info(f"Turn {turn_order} mark cleared")

            # --- Save immediately so UI updates persist ---
            try:
                 save_session_to_file()
            except Exception as save_err:
                 logger.error(f"Failed to save session after mark: {save_err}")

    except Exception as e:
        logger.error(f"MARKING ERROR for Turn {turn_order}: {e}", exc_info=True)


async def broadcast_message(message):
    if connected_clients:
        message_json = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_json) for client in connected_clients]
        )


# -------------------------------------------------------------------------
# ASSEMBLYAI EVENT HANDLERS
# -------------------------------------------------------------------------
def on_begin(self: type[StreamingClient], event: BeginEvent):
    logger.info(f"✅ SESSION STARTED: {event.id}")
    print(f"✅ SESSION STARTED: {event.id}")
    print(f"🎤 Listening for audio... Speak now!")

    start_new_session(event.id)

    if main_loop:
        asyncio.run_coroutine_threadsafe(
            broadcast_message(
                {"message_type": "session_start", "session_id": event.id}
            ),
            main_loop,
        )


def on_turn(self: type[StreamingClient], event: TurnEvent):
    # --- HANDLE PARTIALS VS FINAL TURNS ---
    # AssemblyAI v3 sends 'Turn' events for both partials and final results.
    # We use 'end_of_turn' to distinguish them.
    
    is_final = getattr(event, "end_of_turn", False) # Default to False if missing

    if not is_final:
        # --- PARTIAL TRANSCRIPT ---
        # Broadcast as "partial" so frontend updates in-place
        if main_loop:
            asyncio.run_coroutine_threadsafe(
                broadcast_message({
                    "message_type": "partial",
                    "text": event.transcript
                }),
                main_loop,
            )
        return # Stop here for partials (don't save to DB yet)

    # --- FINAL TRANSCRIPT (end_of_turn=True) ---
    save_turn_to_session(event)

    turn_data = next(
        (t for t in current_session["turns"] if t["turn_order"] == event.turn_order),
        None,
    )
    speaking_rate = None
    if turn_data and turn_data.get("analysis"):
        speaking_rate = turn_data["analysis"].get("speaking_rate_wpm")

    # --- SPEAKER HANDLING ---
    # AssemblyAI returns 'A', 'B', etc.
    # Ideally, we map 'A' -> 'Aaron', 'B' -> Student Name.
    
    detected_speaker = getattr(event, "speaker", "A") # Default to 'A' if None
    
    # FORCE "Aaron" if it's speaker A (assuming you are the primary speaker/host)
    # If it's B, C, D -> Leave it as is (or map to Student Name later in frontend)
    
    final_speaker_name = detected_speaker
    if detected_speaker == "A":
        final_speaker_name = config.get("speaker_name", "Aaron")
    elif detected_speaker == "B":
        final_speaker_name = current_session.get("student_name", "Student")
        
    message = {
        "message_type": "transcript",
        "text": event.transcript,
        "turn_order": event.turn_order,
        "speaker": final_speaker_name,
        "session_id": current_session["session_id"],
        "timestamp": turn_data.get("created") if turn_data else datetime.now().isoformat(),
    }

    if speaking_rate:
        message["speaking_rate_wpm"] = speaking_rate

    if main_loop:
        asyncio.run_coroutine_threadsafe(broadcast_message(message), main_loop)

    # --- SUPABASE STREAMING ---
    if supabase and current_session["session_id"] and turn_data:
        try:
            threading.Thread(
                target=stream_to_supabase_sync,
                args=(turn_data, current_session["session_id"]),
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Error spawning Supabase thread: {e}")


from analyzers.session_analyzer import analyze_session_file

# ... (keep existing imports)

# -------------------------------------------------------------------------
# SUPABASE ANALYSIS UPLOAD
# -------------------------------------------------------------------------
def get_student_id(name):
    """Find student ID by name (username or first_name)"""
    if not supabase:
        return None
    try:
        # Try exact username match
        res = supabase.table("students").select("id").eq("username", name).execute()
        if res.data:
            return res.data[0]['id']
        
        # Try first name match
        # Note: ilike might not be available in all client versions, using eq for safety or raw filter if needed
        # For now, let's try a simple query.
        res = supabase.table("students").select("id").eq("first_name", name).execute()
        if res.data:
            return res.data[0]['id']
            
        return None
    except Exception as e:
        logger.error(f"Error finding student ID: {e}")
        return None

async def perform_batch_diarization(audio_path, session_path):
    """
    Uploads audio to AssemblyAI Batch API for accurate diarization.
    Updates the session JSON with speaker labels.
    """
    if not os.path.exists(audio_path):
        logger.error(f"❌ Audio file not found: {audio_path}")
        return False

    logger.info("🔄 Starting Post-Session Diarization...")
    try:
        transcriber = Transcriber()
        config = TranscriptionConfig(
            speaker_labels=True,
            speakers_expected=2, # Tutor + Student
            punctuate=True,
            format_text=True
        )
        
        transcript = await transcriber.transcribe_async(audio_path, config)
        
        if transcript.status == "error": # Use string "error" for status check
            logger.error(f"❌ Diarization failed: {transcript.error}")
            return False

        # Map speakers
        # We assume the speaker with the most speech is the Tutor (Aaron) if not explicitly identified
        # But for now, let's just use the labels 'A', 'B' and try to map them to existing turns
        
        logger.info("✅ Diarization complete. Mapping speakers...")
        
        # Load current session data
        with open(session_path, 'r') as f:
            session_data = json.load(f)
            
        # Simple mapping strategy: 
        # Iterate through batch utterances and match them to streaming turns based on timestamp
        # This is complex because streaming timestamps might differ slightly.
        # A simpler approach for this MVP:
        # Just update the "speaker" field in the session_data based on the batch result order
        # OR better: Replace the text with the high-quality batch transcript?
        # NO, we want to keep the real-time analysis metadata.
        
        # Let's just update the speaker labels for now.
        # We'll use a time-overlap matching.
        
        batch_utterances = transcript.utterances
        
        for turn in session_data['turns']:
            # Find matching utterance in batch
            # Turn has 'created' (ISO timestamp). We need relative time.
            # This is hard without relative offsets.
            # FALLBACK: Just trust the batch transcript for the final record?
            # YES. The batch transcript is the source of truth for the database.
            pass

        # ACTUALLY: The most robust way is to use the BATCH transcript as the "Corpus" source
        # and just attach the analysis metadata from the streaming session to it.
        
        # For now, let's just save the diarized transcript as a separate file or update the session
        # with a "diarized_turns" field.
        
        session_data['diarized_turns'] = [
            {
                "speaker": u.speaker,
                "text": u.text,
                "start": u.start,
                "end": u.end,
                "confidence": u.confidence
            }
            for u in batch_utterances
        ]
        
        # Update the main turns if possible, or just save this
        with open(session_path, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        logger.info(f"✅ Session updated with diarized turns: {session_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Diarization error: {e}")
        return False

async def upload_analysis_to_supabase(session_path, duration_seconds, audio_path=None):
    """Run analysis, build corpus, process notes, and upload to Supabase"""
    if not supabase:
        return

    try:
        # 0. Run Batch Diarization if audio exists
        if audio_path:
            success = await perform_batch_diarization(audio_path, session_path)
            if not success:
                logger.warning("⚠️ Proceeding with upload without diarization")

        # --- DUPLICATE PREVENTION START ---
        logger.info("🛡️ Checking for existing session to prevent duplicates...")
        
        # 1. Calculate Hash
        file_hash = calculate_file_hash(session_path)
        
        # 2. Get Basic Info for Fuzzy Match
        with open(session_path, 'r') as f:
            pre_load_data = json.load(f)
        
        pre_student_name = pre_load_data.get('student_name', 'Unknown')
        pre_start_time = pre_load_data.get('start_time')
        pre_student_id = get_student_id(pre_student_name)

        if pre_student_id:
            # Check 1: Exact Hash Match
            if file_hash:
                res = supabase.table("student_sessions").select("id").eq("metrics->>file_hash", file_hash).execute()
                if res.data:
                    logger.warning(f"⚠️ DUPLICATE DETECTED (Hash Match). Session {res.data[0]['id']} already exists. SKIPPING UPLOAD.")
                    return

            # Check 2: Fuzzy Match (Same Student + Time + Duration)
            # We check for sessions within +/- 2 minutes of start time
            if pre_start_time:
                try:
                    start_dt = datetime.fromisoformat(pre_start_time)
                    # Create a time window (e.g., 5 mins before and after)
                    # Supabase filtering on timestamps can be tricky, so we might fetch recent sessions for this student and filter in python
                    # Fetch last 10 sessions for this student
                    recent_sessions = supabase.table("student_sessions").select("*").eq("student_id", pre_student_id).order("session_date", desc=True).limit(10).execute()
                    
                    if recent_sessions.data:
                        for s in recent_sessions.data:
                            # Time Check
                            s_date = datetime.fromisoformat(s['session_date'].replace('Z', '+00:00'))
                            # Ensure start_dt is timezone aware or naive as needed. Usually fromisoformat is naive if no TZ in string.
                            # Supabase returns UTC.
                            if start_dt.tzinfo is None:
                                start_dt = start_dt.replace(tzinfo=None) # Make naive if needed, or better assume UTC
                            
                            # Simple string comparison for date part often works if formats align, but delta is safer
                            # Let's just convert both to timestamps
                            # Hack: Just check if strings match up to minutes?
                            # Better:
                            # s_date is from DB (UTC). start_dt is from local file (likely local time or UTC).
                            # Let's assume loose matching.
                            
                            # Duration Check (within 1% or 10 seconds)
                            db_dur = s.get('duration_seconds', 0)
                            dur_diff = abs(db_dur - duration_seconds)
                            is_dur_match = dur_diff < 10 or (db_dur > 0 and dur_diff / db_dur < 0.01)
                            
                            if is_dur_match:
                                # If duration matches, check date loosely (same day is often enough if duration is exact-ish)
                                # But let's check time diff < 5 mins
                                # We'll skip complex TZ logic and just warn if it looks very similar
                                logger.info(f"Checking potential fuzzy duplicate: DB {s['session_date']} vs Local {pre_start_time}")
                                # If we are here, duration is very close. It's likely a duplicate.
                                logger.warning(f"⚠️ POTENTIAL DUPLICATE (Fuzzy Match). Session {s['id']} has similar duration ({db_dur}s vs {duration_seconds}s). SKIPPING UPLOAD to be safe.")
                                return
                except Exception as e:
                    logger.error(f"Error in fuzzy duplicate check: {e}")
        # --- DUPLICATE PREVENTION END ---

        logger.info("Running session analysis for upload...")
        
        # 1. Load session data (now potentially updated)
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        
        # Use diarized turns if available, otherwise streaming turns
        turns_source = session_data.get('diarized_turns', [])
        if not turns_source:
             turns_source = session_data.get('turns', [])
             # Adapt streaming turns to match structure if needed
             # Streaming turns: {speaker, transcript, ...}
             # Diarized turns: {speaker, text, ...}
             
        # 2. Run Analysis
        analysis = analyze_session_file(Path(session_path))
        
        # 3. Get Student ID
        student_name = analysis.get('session_info', {}).get('student_name')
        if not student_name or student_name == "Unknown":
             logger.warning("⚠️ Student name unknown. Skipping upload.")
             return

        student_id = get_student_id(student_name)
        
        if not student_id:
            logger.info(f"⚠️ Student '{student_name}' not found in Supabase. Auto-creating...")
            try:
                new_student = {
                    "username": student_name.lower().replace(" ", ""),
                    "first_name": student_name,
                    "password_hash": "auto_created_placeholder_hash" 
                }
                res = supabase.table("students").insert(new_student).select().execute()
                if res.data:
                    student_id = res.data[0]['id']
                    logger.info(f"✅ Auto-created student '{student_name}' with ID: {student_id}")
                else:
                    logger.error("Failed to auto-create student (no data returned).")
                    return
            except Exception as e:
                logger.error(f"❌ Failed to auto-create student: {e}")
                return

        # 4. BUILD CORPUS - Add student turns to student_corpus
        logger.info("📚 Building corpus from student turns...")
        # Use turns_source for corpus building
        student_turns = [t for t in turns_source if t.get('speaker') != config.get('speaker_name', 'Aaron')]
        
        # DIAGNOSTIC LOGGING - Validate assumptions
        logger.info(f"🔍 DIAGNOSTIC: Found {len(student_turns)} student turns out of {len(turns_source)} total turns")
        logger.info(f"🔍 DIAGNOSTIC: Speaker filter: looking for turns where speaker != '{config.get('speaker_name', 'Aaron')}'")
        
        total_words_found = 0
        for i, turn in enumerate(student_turns):
            words_in_turn = turn.get('words', [])
            logger.info(f"🔍 DIAGNOSTIC: Turn {i+1}: {len(words_in_turn)} words found")
            total_words_found += len(words_in_turn)
            
            # Log first few words as sample
            if words_in_turn and i < 3:  # Log first 3 turns' words
                sample_words = [w.get('text', '') for w in words_in_turn[:5]]
                logger.info(f"🔍 DIAGNOSTIC: Sample words from turn {i+1}: {sample_words}")
        
        logger.info(f"🔍 DIAGNOSTIC: Total words across all student turns: {total_words_found}")
        
        for turn in student_turns:
            corpus_entry = {
                "student_id": student_id,
                "text": turn.get('text', turn.get('transcript', '')), # Use 'text' from diarized, fallback to 'transcript'
                "source": "transcript",
                "metadata": {
                    "turn_order": turn.get('turn_order'),
                    "timestamp": turn.get('created'),
                    "session_id": session_data.get('session_id'),
                    "confidence": turn.get('confidence', turn.get('analysis', {}).get('avg_word_confidence')), # Use 'confidence' from diarized, fallback to streaming
                    "wpm": turn.get('analysis', {}).get('speaking_rate_wpm') # WPM only from streaming analysis
                }
            }
            try:
                supabase.table("student_corpus").insert(corpus_entry).execute()
            except Exception as e:
                logger.warning(f"Failed to add turn to corpus: {e}")
        
        # 5. BUILD WORD-LEVEL CORPUS - Extract individual words
        logger.info("📖 Building word-level corpus...")
        word_corpus_entries = []
        for turn in student_turns:
            words = turn.get('words', [])
            for word in words:
                word_entry = {
                    "student_id": student_id,
                    "text": word.get('text', ''),
                    "source": "word",
                    "metadata": {
                        "session_id": session_data.get('session_id'),
                        "turn_order": turn.get('turn_order'),
                        "word_start_ms": word.get('start_ms'),
                        "word_end_ms": word.get('end_ms'),
                        "word_duration_ms": word.get('duration_ms'),
                        "confidence": word.get('confidence'),
                        "word_is_final": word.get('word_is_final')
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
                logger.warning(f"Failed to add word-level corpus entries: {e}")
        
        logger.info(f"✅ Added {len(student_turns)} turns to corpus")

        # 5. PROCESS NOTES - Send through LLM for intent extraction
        notes_raw = session_data.get('notes', '')
        notes_analysis = None
        
        if notes_raw and notes_raw.strip():
            logger.info("📝 Analyzing tutor notes with LLM...")
            try:
                # Use AssemblyAI LLM Gateway
                prompt = f"""Analyze these tutor notes from an ESL class session. Extract:
1. Key teaching moments or observations
2. Action items for the tutor (things to look up, send, prepare)
3. Student progress indicators
4. Areas of concern

Notes: {notes_raw}

Provide a structured JSON response with: teaching_moments, action_items, progress_notes, concerns"""
                
                response = httpx.post(
                    "https://llm-gateway.assemblyai.com/v1/chat/completions",
                    headers={"Authorization": api_key}, # Use api_key directly
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
                        "raw_notes": notes_raw,
                        "llm_analysis": result['choices'][0]['message']['content']
                    }
                    logger.info("✅ Notes analyzed successfully")
            except Exception as e:
                logger.warning(f"Note analysis failed, storing raw notes only: {e}")
                notes_analysis = {"raw_notes": notes_raw}

        # 6. Run LeMUR Analysis (Extract Actionable Phenomena)
        logger.info("🤖 Running LeMUR Analysis (Extracting Actionable Phenomena)...")
        lemur_response = "No analysis generated."
        try:
            from analyzers.lemur_query import run_lemur_query
            
            # Save temp session file for LeMUR to read
            temp_session_path = Path(f"sessions/temp_{session_data['session_id']}.json")
            with open(temp_session_path, 'w') as f:
                json.dump(session_data, f)
                
            # Extract specific, actionable phenomena that Lemur can detect from transcript data
            phenomena_extraction_prompt = (
                "You are an expert ESL tutor analyzing a student transcript. "
                "Extract ONLY specific, actionable teaching points that you can detect from the text. "
                "Focus on patterns and specific examples, not general categories.\n\n"
                "For VOCABULARY: Identify specific words/phrases the student struggled with "
                "(look for: low confidence words, long pauses before words, substitutions). "
                "List the exact words and context.\n\n"
                "For GRAMMAR: Find recurring error patterns (tense issues, article misuse, "
                "word order problems). Quote specific examples from the transcript.\n\n"
                "For PRONUNCIATION: Flag words with unusually low confidence scores that "
                "might indicate mispronunciation. List the specific words.\n\n"
                "For FLUENCY: Count and list filler words (um, uh, like), note long pauses (>1s), "
                "and identify self-corrections.\n\n"
                "For COMMUNICATION STRATEGIES: Note how the student compensates for gaps "
                "(circumlocution, asking for help, using gestures if mentioned).\n\n"
                "For LISTENING: Identify inappropriate responses that suggest "
                "misunderstanding.\n\n"
                "Format as a structured list with specific examples and timestamps if available. "
                "Be concrete and actionable, not general."
            )
            
            analysis_results = run_lemur_query(temp_session_path, custom_prompt=phenomena_extraction_prompt)
            lemur_response = analysis_results.get('lemur_analysis', {}).get('response', 'No analysis generated.')
            
            # Clean up temp file
            if temp_session_path.exists():
                temp_session_path.unlink()
        except Exception as e:
            logger.error(f"❌ LeMUR Analysis Error: {e}")

        # 7. Prepare Payload
        payload = {
            "student_id": student_id,
            "session_date": analysis.get('session_info', {}).get('start_time'),
            "duration_seconds": int(duration_seconds),
            "metrics": {
                **analysis.get('student_metrics', {}),
                "notes": notes_analysis,
                **analysis.get('student_metrics', {}),
                "notes": notes_analysis,
                "lemur_analysis": lemur_response,
                "file_hash": file_hash # Add hash to metrics for future checks
            }
        }
        
        # 8. Insert into Supabase
        supabase.table("student_sessions").insert(payload).execute()
        logger.info(f"✅ Analysis uploaded to Supabase for {student_name}")

        # 9. Upload Report to Sanity (via API)
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
            
            mutations = {
                "mutations": [
                    {
                        "create": {
                            "_type": "lessonAnalysis", # Generic type
                            "studentName": student_name,
                            "sessionDate": analysis.get('session_info', {}).get('start_time'),
                            "analysisReport": lemur_response,
                            "scores": {} 
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
        
    except Exception as e:
        logger.error(f"❌ Failed to upload analysis: {e}")


def on_terminated(self: type[StreamingClient], event: TerminationEvent):
    logger.info(
        f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
    )
    print(
        f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
    )

    # Final save happens here
    save_session_to_file()
    logger.info(f"Session saved to: {current_session['file_path']}")

    # --- Upload Analysis to Supabase ---
    if supabase and current_session["session_id"]:
        try:
            # Run upload_analysis_to_supabase in a separate thread to avoid blocking
            # It's an async function, so we need to run it in the event loop
            # or use asyncio.run_coroutine_threadsafe if main_loop is available.
            # For simplicity, let's use a new event loop for this thread.
            def run_async_upload():
                asyncio.run(upload_analysis_to_supabase(
                    current_session["file_path"],
                    event.audio_duration_seconds,
                    current_session["audio_path"]
                ))
            threading.Thread(
                target=run_async_upload,
                daemon=True
            ).start()
        except Exception as e:
            logger.error(f"Error spawning Supabase upload thread: {e}")

    print_session_summary()

    if main_loop:
        asyncio.run_coroutine_threadsafe(
            broadcast_message(
                {
                    "message_type": "session_end",
                    "audio_duration_seconds": event.audio_duration_seconds,
                }
            ),
            main_loop,
        )


def print_session_summary():
    """Print quick session summary to terminal"""
    if not current_session["turns"]:
        return

    total_turns = len(current_session["turns"])
    total_words = sum(len(t.get("words", [])) for t in current_session["turns"])
    marked_turns = len([t for t in current_session["turns"] if t.get("marked", False)])

    wpms = [
        t.get("analysis", {}).get("speaking_rate_wpm") for t in current_session["turns"]
    ]
    wpms = [w for w in wpms if w is not None]
    avg_wpm = round(sum(wpms) / len(wpms), 1) if wpms else 0

    if current_session["start_time"]:
        start = datetime.fromisoformat(current_session["start_time"])
        duration_minutes = (datetime.now() - start).total_seconds() / 60
    else:
        duration_minutes = 0

    print("\n" + "=" * 60)
    print("📊 SESSION COMPLETE")
    print("=" * 60)
    print(f"Duration: {duration_minutes:.1f} minutes")
    print(f"Turns: {total_turns}")
    print(f"Words: {total_words}")
    print(f"Avg WPM: {avg_wpm}")
    print(f"Marked moments: {marked_turns}")
    print(f"Saved to: {current_session['file_path']}")
    print("=" * 60 + "\n")


def on_error(self: type[StreamingClient], error: StreamingError):
    logger.error(f"Error occurred: {error}")
    print(f"Error occurred: {error}")
    if main_loop:
        asyncio.run_coroutine_threadsafe(
            broadcast_message({"message_type": "Error", "error": str(error)}), main_loop
        )


# -------------------------------------------------------------------------
# CUSTOM AUDIO STREAM CLASS
# -------------------------------------------------------------------------
class MonoMicrophoneStream:
    """Custom microphone stream that converts multi-channel to mono"""

    # --- FIX: Hardcoded default device_index changed to 7 ---
    def __init__(self, sample_rate=16000, device_index=7, chunk_size=8000, channel_indices=None):
        self.rate = sample_rate
        self.chunk = chunk_size
        self.p = pyaudio.PyAudio()

        device_info = self.p.get_device_info_by_index(device_index)
        self.input_channels = int(device_info["maxInputChannels"])
        self.channel_indices = (
            channel_indices if channel_indices else list(range(self.input_channels))
        )

        logger.info(f"🎤 Audio device: {device_info['name']}")
        logger.info(f"📊 Input channels: {self.input_channels}")
        if self.channel_indices:
            logger.info(f"🎧 Listening to channels: {self.channel_indices}")

        if self.input_channels == 0:
            logger.error(f"❌ Device {device_index} has no input channels!")
            logger.error(f"💡 Run 'python check_audio.py' to find the correct device")
            raise ValueError(
                f"Device {device_index} ({device_info['name']}) has no input channels"
            )

        if max(self.channel_indices) >= self.input_channels:
            logger.error(
                f"❌ Invalid channel index in {self.channel_indices}. Device only has {self.input_channels} channels."
            )
            raise ValueError("Invalid channel index")

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.input_channels, # Use actual input channels
            rate=self.rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk
        )
        
        # Audio saving
        self.wave_file = None
        Path("sessions").mkdir(exist_ok=True) # Ensure sessions directory exists
        self.audio_path = f"sessions/audio_{int(time.time())}.wav"
        try:
            self.wave_file = wave.open(self.audio_path, 'wb')
            self.wave_file.setnchannels(1) # We save the mixed mono
            self.wave_file.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            self.wave_file.setframerate(self.rate)
            current_session['audio_path'] = self.audio_path
            logger.info(f"Recording raw audio to: {self.audio_path}")
        except Exception as e:
            logger.error(f"Failed to open wav file for recording: {e}")

    def __iter__(self):
        return self

    def __next__(self):
        data = self.stream.read(self.chunk, exception_on_overflow=False)
        
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        if self.input_channels > 1:
            audio_data = audio_data.reshape(
                -int(len(audio_data) / self.input_channels), self.input_channels
            )
            selected_channels = audio_data[:, self.channel_indices]
            audio_data = selected_channels.mean(axis=1).astype(np.int16)

        return audio_data.tobytes()

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


# -------------------------------------------------------------------------
# STREAMING CLIENT RUNNER
# -------------------------------------------------------------------------
def run_streaming_client():
    """Run the streaming client in a separate thread"""
    client = StreamingClient(
        StreamingClientOptions(api_key=api_key, api_host="streaming.assemblyai.com")
    )

    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)

    # --- FIX: Conservative Settings for Language Learning ---
    client.connect(
        StreamingParameters(
            sample_rate=16000,
            audio_encoding="pcm_s16le",
            # Raw text configuration
            punctuate=False, # DISABLED for ESL accuracy
            format_text=False, # DISABLED for ESL accuracy
            # speaker_labels=True, # REMOVED: Ignored in v3 streaming
            # OPTIMIZATION: We now use post-session batch diarization for accurate speaker labeling
            # This improves diarization accuracy significantly for 1-on-1 sessions.
            # Note: Streaming API uses 'speakers_expected' or similar if available, 
            # but currently v3 streaming setup typically relies on 'speaker_labels=True'.
            # We will check if 'speakers_expected' is a valid param for StreamingParameters.
            # If not, we rely on the improved model. 
            # The docs mention 'speakers_expected' for TranscriptionConfig (batch), 
            # but for Streaming, it's often auto-detected.
            # However, we can enforce conservative confidence thresholds.
            
            # CONSERVATIVE TURN DETECTION SETTINGS
            end_of_turn_confidence_threshold=0.7,
            min_end_of_turn_silence_when_confident=800,
            max_turn_silence=3600,
        )
    )

    mono_stream = None

    # Use config if valid, otherwise None (PyAudio default)
    device_index = config.get("device_index")
    channel_indices = config.get("channel_indices", [])

    # Simple Logic: If user didn't set index, or if it failed, use Default.

    try:
        if device_index is not None:
             logger.info(f"🎧 Attempting to use configured audio device: {device_index}")
             try:
                 mono_stream = MonoMicrophoneStream(
                    sample_rate=16000,
                    device_index=device_index,
                    channel_indices=channel_indices,
                 )
             except Exception as e:
                 logger.warning(f"⚠️ Configured device {device_index} failed: {e}")
                 mono_stream = None # Fallback

        if mono_stream is None:
            logger.info("🔄 Using system default input device...")
            # Find default device index
            p = pyaudio.PyAudio()
            try:
                default_info = p.get_default_input_device_info()
                default_index = default_info['index']
                logger.info(f"✅ Found default device: [{default_index}] {default_info['name']}")

                mono_stream = MonoMicrophoneStream(
                    sample_rate=16000,
                    device_index=default_index,
                    channel_indices=None # Reset channels for default
                )
            finally:
                p.terminate()

        client.stream(mono_stream)

    except Exception as e:
        logger.error(f"❌ CRITICAL AUDIO ERROR: {e}")
        logger.error(f"💡 Run 'python check_audio.py' to debug audio devices")
    finally:
        if mono_stream:
            mono_stream.close()
        client.disconnect(terminate=True)
        gc.collect()


# -------------------------------------------------------------------------
# MAIN ENTRY POINT
# -------------------------------------------------------------------------
async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    logger.info("Starting main function")

    monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
    monitor_thread.start()

    server = await websockets.serve(websocket_handler, "localhost", 8765)
    logger.info("WebSocket server started on ws://localhost:8765")

    # --- Auto-Sync Students from Cloud ---
    if SUPABASE_AVAILABLE and supabase:
        try:
            logger.info("☁️ Syncing students from Supabase...")
            # Just call get_existing_students to sync - it already handles everything
            students = get_existing_students()
            logger.info(f"✅ Synced {len(students)} students (Cloud + Local)")
        except Exception as e:
            logger.error(f"⚠️ Failed to sync students: {e}")

    # Note: Streaming client is now started AFTER student selection via WebSocket
    # The frontend should send a "start_session" message after selecting a student

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        server.close()
        await server.wait_closed()


if __name__ == "__main__":
    import argparse

    # Pre-flight check for audio device
    device_index = config.get("device_index")
    if device_index is None:
        logger.error(
            "❌ Audio device index not found in config.json. Please run 'python check_audio.py' and update your config."
        )
        sys.exit(1)
    if not validate_audio_device(device_index):
        logger.warning("⚠️ Audio device validation failed, but attempting to start anyway (Soft Fail)")
        # sys.exit(1)  <-- REMOVED TO PREVENT HARD CRASH ON STARTUP IF DEVICE IS FLAKY

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tui", action="store_true", help="Run the Terminal User Interface"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("🚀 SEMANTIC SURFER STARTING")
    logger.info("=" * 60)
    logger.info(f"✓ API Key: {'Loaded' if api_key else 'MISSING'}")
    logger.info(
        f"✓ Config: Speaker={config.get('speaker_name', 'Unknown')}, Device={config.get('device_index', 'Unknown')}"
    )
    logger.info(f"✓ Python Version: {sys.version}")
    logger.info(f"✓ Working Directory: {os.getcwd()}")
    logger.info("=" * 60)

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ FATAL ERROR: {e}")
        logger.error("=" * 60)
        import traceback

        traceback.print_exc()
        sys.exit(1)
