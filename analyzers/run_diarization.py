#!/usr/bin/env python3
"""
Phase 2, Step 1: Diarization
Takes a session.json file, finds its associated .wav file,
uploads it to AssemblyAI's async API with speaker labels,
and saves the new diarized transcript.
"""

import assemblyai as aai
import os
import sys
import json
from pathlib import Path
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment
api_key = os.getenv('ASSEMBLYAI_API_KEY')
if not api_key:
    logger.error("❌ ASSEMBLYAI_API_KEY not found in environment. Cannot run diarization.")
    sys.exit(1)

aai.settings.api_key = api_key

def run_diarization(original_session_path: Path) -> Path:
    """
    Transcribes an audio file with speaker diarization and
    saves the result to a new JSON file.
    """

    # 1. Open the original session.json
    try:
        with open(original_session_path, 'r') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"❌ Failed to open session file: {original_session_path}")
        logger.error(e)
        raise

    audio_path_str = session_data.get("audio_file_path")
    if not audio_path_str:
        logger.error(f"❌ 'audio_file_path' not found in {original_session_path}")
        raise ValueError("Missing audio_file_path in session JSON")

    audio_path = Path(audio_path_str)
    if not audio_path.exists():
        logger.error(f"❌ Audio file not found: {audio_path}")
        raise FileNotFoundError(f"Audio file {audio_path} does not exist")

    # 2. Configure and run transcription
    logger.info(f"Uploading {audio_path} for diarization...")
    config = aai.TranscriptionConfig(
        speaker_labels=True  # <-- THE CRITICAL SETTING
    )
    transcriber = aai.Transcriber()

    try:
        transcript = transcriber.transcribe(str(audio_path), config)
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        raise

    if transcript.status == aai.TranscriptStatus.error:
        logger.error(f"❌ Transcription failed: {transcript.error}")
        raise Exception(f"Transcription error: {transcript.error}")

    # 3. Save the new diarized JSON
    # We save it with a new name to avoid overwriting the original
    diarized_output_path = original_session_path.parent / f"{original_session_path.stem}_diarized.json"

    # We save the *full* transcript object as JSON
    # We use .json() method from the SDK model
    try:
        with open(diarized_output_path, 'w') as f:
            f.write(transcript.json(indent=2))

        logger.info(f"✅ Diarized transcript saved to: {diarized_output_path}")
        return diarized_output_path

    except Exception as e:
        logger.error(f"❌ Failed to save diarized JSON: {e}")
        raise

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_diarization.py <original_session.json>")
        sys.exit(1)

    session_file = Path(sys.argv[1])

    if not session_file.exists():
        print(f"Error: File not found: {session_file}")
        sys.exit(1)

    try:
        run_diarization(session_file)
    except Exception as e:
        logger.error(f"Diarization process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
