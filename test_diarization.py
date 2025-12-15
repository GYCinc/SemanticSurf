#!/usr/bin/env python3
"""
Simple Audio → AssemblyAI → Diarized Transcript
One command: python test_diarization.py /path/to/audio.mp3
"""

import os
import sys
import assemblyai as aai
from dotenv import load_dotenv

load_dotenv()

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def transcribe(audio_path: str):
    print(f"📤 Uploading: {audio_path}")
    
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=2,
        punctuate=True,
        format_text=False  # Keep fillers
    )
    
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path, config)
    
    if transcript.status == "error":
        print(f"❌ Error: {transcript.error}")
        return
    
    print(f"\n✅ Transcription Complete!")
    print(f"Duration: {transcript.audio_duration}s")
    print(f"Confidence: {transcript.confidence:.2%}")
    print(f"Speakers: {len(set(u.speaker for u in transcript.utterances))}")
    
    print(f"\n{'='*60}")
    print("DIARIZED TRANSCRIPT")
    print(f"{'='*60}\n")
    
    for utterance in transcript.utterances:
        print(f"[Speaker {utterance.speaker}]: {utterance.text}\n")
    
    return transcript

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_diarization.py /path/to/audio.mp3")
        sys.exit(1)
    
    transcribe(sys.argv[1])
