#!/usr/bin/env python3
"""
Phase 2, Step 1: Diarization (DUAL-PASS PROTOCOL)
Takes a session.json file, finds its associated .wav file,
uploads it ONCE to AssemblyAI, and runs two transcription passes:
1. Diarization Pass (Structure)
2. Raw Pass (Content)
Then merges them to produce a Diarized Raw Transcript.
"""

import assemblyai as aai
import os
import sys
import json
from pathlib import Path
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RunDiarization")

# Load API key from environment
api_key = os.getenv('ASSEMBLYAI_API_KEY')
if not api_key:
    logger.error("❌ ASSEMBLYAI_API_KEY not found in environment. Cannot run diarization.")
    sys.exit(1)

aai.settings.api_key = api_key

def run_diarization(original_session_path: Path) -> Path:
    """
    Transcribes an audio file using the Dual-Pass Protocol.
    """

    # 1. Open the original session.json
    try:
        with open(original_session_path, 'r') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"❌ Failed to open session file: {original_session_path}")
        logger.error(e)
        raise

    audio_path_str = session_data.get("audio_file_path") or session_data.get("audio_path")
    if not audio_path_str:
        logger.error(f"❌ 'audio_file_path' not found in {original_session_path}")
        raise ValueError("Missing audio_file_path in session JSON")

    audio_path = Path(audio_path_str)
    if not audio_path.exists():
        logger.error(f"❌ Audio file not found: {audio_path}")
        raise FileNotFoundError(f"Audio file {audio_path} does not exist")

    # 2. Upload Once
    logger.info(f"📤 Uploading {audio_path}...")
    transcriber = aai.Transcriber()
    upload_url = transcriber.upload_file(str(audio_path))
    logger.info(f"✅ Uploaded to: {upload_url}")

    # 3. Pass 1: Diarization (Structural)
    logger.info("🧠 Pass 1: Extracting Speaker Labels (Punctuation=ON)...")
    config_diar = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.universal,
        language_code="en_us",
        speaker_labels=True,
        speakers_expected=2,
        punctuate=True,
        format_text=False
    )

    # 4. Pass 2: Raw (Content)
    logger.info("🧠 Pass 2: Extracting Raw Content (Punctuation=OFF)...")
    config_raw = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.universal,
        language_code="en_us",
        speaker_labels=False,
        punctuate=False,
        format_text=False,
        disfluencies=True
    )

    # 5. Execute Both
    logger.info("⏳ Waiting for both passes to complete...")
    t_diar = transcriber.transcribe(upload_url, config_diar)
    t_raw = transcriber.transcribe(upload_url, config_raw)

    if t_diar.status == aai.TranscriptStatus.error:
        raise Exception(f"Pass 1 Failed: {t_diar.error}")
    if t_raw.status == aai.TranscriptStatus.error:
        raise Exception(f"Pass 2 Failed: {t_raw.error}")

    # 6. Merge Logic
    logger.info("🔗 Merging Structure and Content...")
    
    # Map diarized words to speakers
    diar_word_map = []
    if t_diar.utterances:
        for utt in t_diar.utterances:
            for w in utt.words:
                diar_word_map.append({'start': w.start, 'end': w.end, 'speaker': utt.speaker})
    
    diar_word_map.sort(key=lambda x: x['start'])

    merged_utterances = []
    current_speaker = None
    current_words = []
    
    # Iterate through RAW words and assign speakers from Diarization map
    diar_idx = 0
    for rw in t_raw.words:
        speaker = "Unknown"
        # Find speaker overlap
        temp_idx = diar_idx
        while temp_idx < len(diar_word_map):
            d = diar_word_map[temp_idx]
            if d['end'] < rw.start:
                diar_idx = temp_idx
                temp_idx += 1
                continue
            if d['start'] > rw.end:
                break
            speaker = d['speaker']
            break
        
        if speaker == "Unknown":
            speaker = current_speaker or "A"

        if speaker != current_speaker:
            if current_words:
                merged_utterances.append({
                    "speaker": current_speaker,
                    "text": " ".join([w['text'] for w in current_words]),
                    "words": current_words,
                    "start": current_words[0]['start'],
                    "end": current_words[-1]['end']
                })
            current_speaker = speaker
            current_words = []
        
        current_words.append({
            "text": rw.text,
            "start": rw.start,
            "end": rw.end,
            "confidence": rw.confidence,
            "speaker": speaker
        })

    if current_words:
        merged_utterances.append({
            "speaker": current_speaker,
            "text": " ".join([w['text'] for w in current_words]),
            "words": current_words,
            "start": current_words[0]['start'],
            "end": current_words[-1]['end']
        })

    # 7. Save merged result
    diarized_output_path = original_session_path.parent / f"{original_session_path.stem}_diarized.json"
    
    final_output = {
        "id": t_raw.id,
        "status": "completed",
        "audio_url": upload_url,
        "text": t_raw.text,
        "utterances": merged_utterances,
        "words": [w for u in merged_utterances for w in u['words']],
        "audio_duration": t_raw.audio_duration,
        "confidence": t_raw.confidence,
        "dual_pass_merged": True
    }

    try:
        with open(diarized_output_path, 'w') as f:
            json.dump(final_output, f, indent=2)

        logger.info(f"✅ Dual-Pass diarized transcript saved to: {diarized_output_path}")
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