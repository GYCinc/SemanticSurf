# Semantic Surfer - Data Storage Guide

## Where Everything Gets Saved

### 📁 Storage Location
```
/Users/thelaw/AssemblyAI/sessions/
├── session_2024-10-30_14-30-15.json
├── session_2024-10-30_15-45-22.json
└── ...
```

**Every session automatically saves to a timestamped JSON file.**

## What Gets Recorded

### ❌ NOT Recorded:
- Audio files (too large, privacy concerns)
- Video
- Screen captures

### ✅ RECORDED (Text Data Only):
- **Raw transcripts** - Exactly what was said
- **Word-level timestamps** - Millisecond precision
- **Confidence scores** - For each word
- **Turn boundaries** - When speaker stops/starts
- **Your marks** - Which lines you tagged
- **Speaker name** - "Aaron" (from config.json)

## Example Session File

```json
{
  "app_name": "Semantic Surfer",
  "session_id": "abc123",
  "speaker": "Aaron",
  "start_time": "2024-10-30T14:30:15.123Z",
  "end_time": "2024-10-30T14:35:42.789Z",
  "total_turns": 45,
  "total_words": 234,
  "turns": [
    {
      "turn_order": 1,
      "transcript": "i go to store yesterday",
      "speaker": "Aaron",
      "end_of_turn": true,
      "end_of_turn_confidence": 0.87,
      "marked": true,
      "mark_type": "all",
      "mark_timestamp": "2024-10-30T14:32:15.234Z",
      "words": [
        {
          "text": "i",
          "start_ms": 1234,
          "end_ms": 1456,
          "duration_ms": 222,
          "confidence": 0.95,
          "word_is_final": true
        },
        {
          "text": "go",
          "start_ms": 1456,
          "end_ms": 1678,
          "duration_ms": 222,
          "confidence": 0.87,
          "word_is_final": true
        }
        // ... more words
      ]
    }
    // ... more turns
  ]
}
```

## File Sizes

- **10-minute session**: ~15KB
- **1-hour session**: ~90KB
- **Daily (5 hours)**: ~450KB
- **Monthly (100 hours)**: ~9MB

**Tiny files! Easy to store, backup, and analyze.**

## Configuring Speaker Name

Edit [`config.json`](config.json:1):

```json
{
  "speaker_name": "Aaron",  // Change to your name
  "app_name": "Semantic Surfer"
}
```

Restart the backend to apply changes.

## What Happens on Shutdown

### Automatic Save
- Session file is saved after EVERY turn (crash-safe)
- Final save happens on shutdown
- All marks are preserved
- Complete metadata included

### Manual Export
- Press **E** in the viewer
- Downloads current session as JSON
- Includes all marks and metadata
- Backup copy for safety

## Using the Data

### For Voice Notes (Your Workflow)
1. Session ends → JSON file saved
2. Open JSON in any text editor
3. Find marked turns (`"marked": true`)
4. Record voice notes for each
5. Fast review process!

### For Analysis
- Import JSON into Python/R/Excel
- Analyze confidence patterns
- Study timing and pauses
- Track improvement over time
- Generate reports

### For Research
- Raw, unformatted data
- Complete metadata
- Reproducible results
- Privacy-compliant (local only)

## Privacy & Compliance

### What Stays Local:
- ✅ All JSON files
- ✅ All transcripts
- ✅ All metadata
- ✅ Your marks

### What Goes to Cloud:
- ⚠️ Audio (sent to AssemblyAI for transcription)
- ⚠️ AssemblyAI processes it and sends back text
- ⚠️ AssemblyAI doesn't store it permanently (check their policy)

### For Student Consent:
- Inform students audio is processed by AssemblyAI
- All transcripts saved locally on your computer
- No permanent cloud storage of their data
- You control all the files

## Backup Strategy

### Recommended:
```bash
# Backup sessions folder
cp -r sessions sessions_backup_$(date +%Y%m%d)

# Or use Time Machine / cloud backup
# sessions/ folder is small enough for any backup solution
```

### Cloud Backup (Optional):
- Dropbox/Google Drive sync
- GitHub private repo
- Any cloud service (files are tiny)

## Data Retention

**You decide!** Files are yours to keep or delete.

Suggested:
- Keep current semester sessions
- Archive old semesters
- Delete after research is complete

---

**All data is TEXT ONLY. No audio files. Privacy-focused. Locally stored.**