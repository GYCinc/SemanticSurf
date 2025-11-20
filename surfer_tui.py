#!/usr/bin/env python3
"""Semantic Surfer - Terminal UI Edition"""
import assemblyai as aai
from typing import Type
from dotenv import load_dotenv
import logging
import os
import json
from datetime import datetime
from pathlib import Path
import pyaudio
import sys
import signal
import threading
from assemblyai.streaming.v3 import (
    BeginEvent, StreamingClient, StreamingClientOptions,
    StreamingError, StreamingEvents, StreamingParameters,
    TurnEvent, TerminationEvent,
)
from audio import MonoMicrophoneStream
from validation import validate_audio_device

from ui.surfer_display import SurferDisplay
from ui.keyboard_handler import KeyboardHandler

load_dotenv()
api_key = os.getenv('ASSEMBLYAI_API_KEY')

logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger(__name__)

config = {}
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except Exception as e:
    config = {"speaker_name": "Speaker", "device_index": 6}

display = None
keyboard = None
current_session = {"session_id": None, "start_time": None, "turns": [], "file_path": None}
selected_line = -1
is_paused = False
file_lock = threading.Lock()

def start_new_session(session_id):
    global current_session
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    Path("sessions").mkdir(exist_ok=True)
    current_session = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat(),
        "turns": [],
        "file_path": f"sessions/session_{timestamp}.json"
    }

def save_turn_to_session(event: TurnEvent):
    words_data = []
    if hasattr(event, 'words') and event.words:
        for word in event.words:
            words_data.append({
                "text": word.text,
                "start_ms": word.start,
                "end_ms": word.end,
                "confidence": word.confidence
            })
    
    speaking_rate = None
    if words_data and len(words_data) > 0:
        turn_duration_ms = words_data[-1]["end_ms"] - words_data[0]["start_ms"]
        if turn_duration_ms > 0:
            speaking_rate = (len(words_data) / turn_duration_ms) * 60000
    
    turn_data = {
        "turn_order": event.turn_order,
        "transcript": event.transcript,
        "speaker": config.get('speaker_name', 'Speaker'),
        "words": words_data,
        "analysis": {
            "speaking_rate_wpm": round(speaking_rate, 2) if speaking_rate else None
        }
    }
    
    existing_turn = next((t for t in current_session["turns"] if t["turn_order"] == event.turn_order), None)
    if existing_turn:
        existing_turn.update(turn_data)
    else:
        current_session["turns"].append(turn_data)
    
    save_session_to_file()

def save_session_to_file():
    if not current_session["file_path"]:
        return
    with file_lock:
        session_data = {
            "session_id": current_session["session_id"],
            "speaker": config.get('speaker_name', 'Speaker'),
            "start_time": current_session["start_time"],
            "end_time": datetime.now().isoformat(),
            "turns": current_session["turns"]
        }
        try:
            with open(current_session["file_path"], 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save: {e}")

def mark_turn(mark_type):
    if not current_session["turns"]:
        return
    turn_index = len(current_session["turns"]) - 1 if selected_line == -1 else selected_line
    if 0 <= turn_index < len(current_session["turns"]):
        turn = current_session["turns"][turn_index]
        if mark_type:
            turn["marked"] = True
            turn["mark_type"] = mark_type
            turn["mark_timestamp"] = datetime.now().isoformat()
        else:
            turn["marked"] = False
            turn["mark_type"] = None
        save_session_to_file()

def on_mark_front(): mark_turn("front")
def on_mark_all(): mark_turn("all")
def on_mark_back(): mark_turn("back")
def on_clear_mark(): mark_turn(None)
def on_pause():
    global is_paused
    is_paused = not is_paused
def on_export():
    if current_session["file_path"]:
        print(f"\n✅ Session: {current_session['file_path']}\n")
def on_quit(): cleanup_and_exit()

def on_begin(self: Type[StreamingClient], event: BeginEvent):
    start_new_session(event.id)
    if display:
        display.set_session_id(event.id)

def on_turn(self: Type[StreamingClient], event: TurnEvent):
    logger.warning(f"Received transcript: {event.transcript}")
    save_turn_to_session(event)
    turn_data = next((t for t in current_session["turns"] if t["turn_order"] == event.turn_order), None)
    speaking_rate = turn_data['analysis'].get('speaking_rate_wpm') if turn_data and turn_data.get('analysis') else None
    if display and not is_paused:
        display.add_transcript(event.transcript, speaking_rate)

def on_terminated(self: Type[StreamingClient], event: TerminationEvent):
    save_session_to_file()

def on_error(self: Type[StreamingClient], error: StreamingError):
    logger.error(f"Error: {error}")

def run_streaming_client():
    client = StreamingClient(StreamingClientOptions(api_key=api_key))
    client.on(StreamingEvents.Begin, on_begin)
    client.on(StreamingEvents.Turn, on_turn)
    client.on(StreamingEvents.Termination, on_terminated)
    client.on(StreamingEvents.Error, on_error)
    client.connect(StreamingParameters(sample_rate=16000, audio_encoding="pcm_s16le"))
    
    mono_stream = None
    try:
        device_index = config.get('device_index', 6)
        channel_indices = config.get('channel_indices', [])
        logger.info(f"🎧 Using audio device index: {device_index}")
        if channel_indices:
            logger.info(f"🎤 Using channel indices: {channel_indices}")

        mono_stream = MonoMicrophoneStream(
            sample_rate=16000,
            device_index=device_index,
            channel_indices=channel_indices
        )
        client.stream(mono_stream)
    except Exception as e:
        logger.error(f"Audio error: {e}")
    finally:
        if mono_stream:
            mono_stream.close()
        client.disconnect(terminate=True)

def cleanup_and_exit():
    global display, keyboard
    if keyboard: keyboard.stop()
    if display: display.stop()
    save_session_to_file()
    sys.exit(0)

def signal_handler(sig, frame):
    cleanup_and_exit()

def main():
    # Pre-flight check for audio device
    device_index = config.get('device_index')
    if device_index is None:
        logger.error("❌ Audio device index not found in config.json. Please run 'python check_audio.py' and update your config.")
        sys.exit(1)
    if not validate_audio_device(device_index):
        sys.exit(1)

    global display, keyboard
    signal.signal(signal.SIGINT, signal_handler)
    
    display = SurferDisplay(speaker_name=config.get('speaker_name', 'Speaker'))
    keyboard = KeyboardHandler()
    
    keyboard.register_callback('7', on_mark_front)
    keyboard.register_callback('8', on_mark_all)
    keyboard.register_callback('9', on_mark_back)
    keyboard.register_callback('5', on_clear_mark)
    keyboard.register_callback('space', on_pause)
    keyboard.register_callback('e', on_export)
    keyboard.register_callback('q', on_quit)
    keyboard.register_callback('ctrl_c', on_quit)
    
    display.show_startup_splash()
    display.start()
    keyboard.start()
    
    try:
        run_streaming_client()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_and_exit()

if __name__ == "__main__":
    if not api_key:
        print("❌ Error: ASSEMBLYAI_API_KEY not found")
        sys.exit(1)
    main()
