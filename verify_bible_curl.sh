#!/bin/bash

API_KEY="$ASSEMBLYAI_API_KEY"
FILE_PATH="sessions/audio_1766132713.wav"

echo "🚀 Starting Bible Verification (CURL Mode)..."

# 1. Upload
echo "📤 Uploading audio..."
UPLOAD_URL=$(curl -s -H "Authorization: $API_KEY" -H "Content-Type: application/octet-stream" --data-binary "@$FILE_PATH" "https://api.assemblyai.com/v2/upload" | grep -o '"upload_url":"[^"']*' | grep -o '[^"']*')

if [ -z "$UPLOAD_URL" ]; then
    echo "❌ Upload failed."
    exit 1
fi
echo "✅ Uploaded: $UPLOAD_URL"

# 2. Transcribe (THE BIBLE CONFIG)
echo "🧠 Requesting Transcription (slam-1, en_us, raw)..."
TRANSCRIPT_RESPONSE=$(curl -s -X POST "https://api.assemblyai.com/v2/transcript" \
    -H "Authorization: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "audio_url": "'"$UPLOAD_URL"'",
        "speech_model": "slam-1",
        "language_code": "en_us",
        "speaker_labels": true,
        "speakers_expected": 2,
        "punctuate": false,
        "format_text": false
    }')

TRANSCRIPT_ID=$(echo $TRANSCRIPT_RESPONSE | grep -o '"id":"[^"']*' | grep -o '[^"']*')
echo "🆔 Transcript ID: $TRANSCRIPT_ID"

# 3. Poll
echo "⏳ Waiting for processing..."
while true; do
    STATUS=$(curl -s -H "Authorization: $API_KEY" "https://api.assemblyai.com/v2/transcript/$TRANSCRIPT_ID" | grep -o '"status":"[^"']*' | grep -o '[^"']*')
    echo "   Status: $STATUS"
    
    if [ "$STATUS" == "completed" ]; then
        break
    elif [ "$STATUS" == "error" ]; then
        echo "❌ Processing failed."
        exit 1
    fi
    sleep 5
done

# 4. Get Result
echo "📥 Downloading result..."
curl -s -H "Authorization: $API_KEY" "https://api.assemblyai.com/v2/transcript/$TRANSCRIPT_ID" > bible_transcript.json

echo "✅ Done! Saved to bible_transcript.json"
