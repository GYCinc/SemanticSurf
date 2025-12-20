#!/bin/bash

API_KEY="$ASSEMBLYAI_API_KEY"
AUDIO_URL="https://storage.googleapis.com/aai-web-samples/news.mp4"

echo "--- BIBLE TEST SUITE ---"
# Payload with slam-1 and PROMPT
curl -s -X POST "https://api.assemblyai.com/v2/transcript" \
    -H "Authorization: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "audio_url": "'$AUDIO_URL'",
        "speech_model": "slam-1",
        "speaker_labels": true,
        "prompt": "Transcribe the audio exactly as heard, including all errors, disfluencies, and without any auto-correction or punctuation."
    }' | jq -c '.error // .status'
