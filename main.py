import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Type

import httpx # Added for LLM Gateway
import assemblyai as aai
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
    try:
        row = {
            "session_id": session_id,
            "speaker": turn_data.get("speaker"),
            "text": turn_data.get("transcript"),
            "turn_order": turn_data.get("turn_order"),
            "confidence": turn_data.get("end_of_turn_confidence"),
            "timestamp": turn_data.get("created") or datetime.now().isoformat(),
            "metadata": {
                "words": turn_data.get("words"),
                "pauses": turn_data.get("pauses"),
                "analysis": turn_data.get("analysis")
            }
        }
        supabase.table("transcripts").insert(row).execute()
    except Exception as e:
        logger.error(f"Supabase Sync Error: {e}")


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
    "turns": [],
    "file_path": None,
}


# -------------------------------------------------------------------------
# LLM ANALYSIS (AssemblyAI Gateway)
# -------------------------------------------------------------------------
async def analyze_turn_with_llm(text, context=""):
    """Analyze a student turn using AssemblyAI LLM Gateway with Tool Calling"""
    if not api_key:
        logger.error("Cannot analyze: Missing AssemblyAI API Key")
        return {"error": "Missing API Key"}

    url = "https://llm-gateway.assemblyai.com/v1/chat/completions"
    headers = {
        "authorization": api_key,
        "content-type": "application/json"
    }

    # Define the schema for the output we want
    tools = [
        {
            "type": "function",
            "function": {
                "name": "submit_language_feedback",
                "description": "Submit structured feedback for a language learner.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["VOCAB_GAP", "GRAMMAR_ERR", "RECAST", "AVOIDANCE", "PRONUNCIATION", "NONE"],
                            "description": "The category of the linguistic issue."
                        },
                        "suggestedCorrection": {
                            "type": "string",
                            "description": "The natural, corrected version of the sentence."
                        },
                        "explanation": {
                            "type": "string",
                            "description": "A concise explanation of the error (max 2 sentences)."
                        }
                    },
                    "required": ["category", "suggestedCorrection", "explanation"]
                }
            }
        }
    ]

    payload = {
        "model": "claude-3-5-haiku-20241022", 
        "messages": [
            {
                "role": "system", 
                "content": "You are an expert ESL tutor. Analyze the last user utterance given the context. Use the 'submit_language_feedback' tool to provide your analysis."
            },
            {
                "role": "user", 
                "content": f"Context:\n{context}\n\nStudent Utterance to Analyze: \"{text}\""
            }
        ],
        "max_tokens": 1000,
        "tools": tools,
        "tool_choice": {"type": "function", "function": {"name": "submit_language_feedback"}}
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            result = response.json()
            
            # Extract tool arguments
            try:
                choice = result["choices"][0]
                if choice["message"].get("tool_calls"):
                    tool_call = choice["message"]["tool_calls"][0]
                    args = json.loads(tool_call["function"]["arguments"])
                    return args
                else:
                    # Fallback if model refused to call tool (rare with tool_choice)
                    logger.warning("LLM did not call tool, falling back to content.")
                    return {"category": "NONE", "suggestedCorrection": text, "explanation": "No specific feedback."}
                    
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                logger.error(f"LLM Response Parsing Error: {e}")
                return {"error": "Failed to parse LLM response"}
                
    except Exception as e:
        logger.error(f"LLM Gateway Error: {e}")
        return {"error": str(e)}


# -------------------------------------------------------------------------
# SESSION MANAGEMENT
# -------------------------------------------------------------------------
def get_existing_students():
    """Scan Supabase transcripts for unique student names"""
    if not supabase:
        logger.warning("⚠️ Supabase not connected. Falling back to local file scan.")
        return get_local_existing_students()

    try:
        # Query Supabase for unique 'speaker' values
        # Using a little hack: select speaker, count(id) to group by
        # Since 'distinct' is not directly exposed in easy python client methods sometimes,
        # we can just fetch speakers and dedupe in python if the dataset is small, 
        # OR use a .rpc() call if we had a postgres function.
        # For now, let's fetch the last 1000 rows and extract speakers. 
        # (Better long term: create a 'students' table or a postgres view)
        
        response = supabase.table("transcripts").select("speaker").order("timestamp", desc=True).limit(1000).execute()
        
        students = set()
        if response.data:
            for row in response.data:
                name = row.get("speaker")
                # Filter out 'Aaron' (the tutor) and None
                if name and "Aaron" not in name: 
                    students.add(name)
        
        # Also merge with local files to be safe
        local_students = get_local_existing_students()
        students.update(local_students)
        
        return sorted(list(students))
        
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
        student_name = config.get("speaker_name", "Speaker")

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

            # --- CRASH FIX: save_session_to_file() call REMOVED to prevent blocking ---

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
def on_begin(self: Type[StreamingClient], event: BeginEvent):
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


def on_turn(self: Type[StreamingClient], event: TurnEvent):
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


def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
    logger.info(
        f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
    )
    print(
        f"Session terminated: {event.audio_duration_seconds} seconds of audio processed"
    )

    # Final save happens here
    save_session_to_file()
    logger.info(f"Session saved to: {current_session['file_path']}")

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


def on_error(self: Type[StreamingClient], error: StreamingError):
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
    def __init__(
        self, sample_rate=16000, device_index=7, chunk_size=8000, channel_indices=None
    ):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.chunk_size = chunk_size
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
            channels=self.input_channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size,
        )

    def __iter__(self):
        return self

    def __next__(self):
        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
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
            punctuate=True, # Enable punctuation for readability
            format_text=True, # Enable formatting (casing, numbers)
            speaker_labels=True, # Enable Speaker Diarization
            # OPTIMIZATION: Provide the exact number of expected speakers (Tutor + Student)
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
    try:
        # Updated default index 7 based on your setup
        device_index = config.get("device_index", 7)
        channel_indices = config.get("channel_indices", [])
        logger.info(f"🎧 Using audio device index: {device_index}")
        if channel_indices:
            logger.info(f"🎤 Using channel indices: {channel_indices}")

        mono_stream = MonoMicrophoneStream(
            sample_rate=16000,
            device_index=device_index,
            channel_indices=channel_indices,
        )
        client.stream(mono_stream)
    except ValueError as e:
        logger.error(f"❌ Audio device error: {e}")
        logger.error(f"💡 Run 'python check_audio.py' to find available devices")
        logger.error(f"💡 Then update config.json with the correct device_index")
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

    streaming_thread = threading.Thread(target=run_streaming_client, daemon=True)
    streaming_thread.start()
    logger.info("Streaming client started in background thread")

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
