# THE ASSEMBLYAI BIBLE (IMMUTABLE LAWS)

## 🚨 ZERO TOLERANCE POLICY
**DO NOT MODIFY THESE SETTINGS WITHOUT EXPLICIT USER AUTHORIZATION.**
Agents routinely break this pipeline by reverting to "default" or "best" settings. This configuration is the result of painful trial and error. **RESPECT IT.**

---

## 1. The Holy Configuration (Batch / Pre-Recorded)
To achieve **Diarization** AND **Raw Reality** (which the API disallows in a single call), we strictly follow the **DUAL-PASS PROTOCOL**.

### Step 1: Upload Audio ONCE
Use `upload_url = transcriber.upload_file(audio_path)` to get a temporary URL.
*   **Why:** Prevents redundant bandwidth usage. We upload the 90MB+ file once and query against it multiple times.
*   **Method:** Explicit `upload_file` (not implicit `transcribe`).

### Step 2: The Diarization Pass (Request A)
**Goal:** Get the **Structure** (Speakers & Timestamps).
**Constraint:** Diarization (`speaker_labels=True`) **REQUIRES** `punctuate=True` per API validation.

```python
config_diarization = aai.TranscriptionConfig(
    speech_model="universal",   # 🔒 MANDATORY. Reliable for diarization.
    language_code="en_us",      # 🔒 MANDATORY. American English.
    speaker_labels=True,        # 🔒 MANDATORY. The whole point.
    speakers_expected=2,        # 🔒 MANDATORY. Tutor + Student.
    punctuate=True,             # 🔒 FORCED ON. Satisfies API constraint.
    format_text=False           # 🔒 OFF. Minimize other formatting.
)
```

### Step 3: The Raw Pass (Request B)
**Goal:** Get the **Content** (Raw Words, "go-ed", "um", "uh").
**Constraint:** Must turn OFF all "AI fixes".

```python
config_raw = aai.TranscriptionConfig(
    speech_model="universal",   # 🔒 MANDATORY. Consistent with Pass A.
    language_code="en_us",      # 🔒 MANDATORY.
    speaker_labels=False,       # 🔒 OFF. Allows punctuate=False.
    punctuate=False,            # 🔒 OFF. Raw Reality.
    format_text=False,          # 🔒 OFF. No casing/number fixes.
    disfluencies=True           # 🔒 ON. Capture 'um', 'uh', 'like'.
)
```

### Step 4: The Merge (The Logic)
1.  **Iterate** through the **Raw Words** (from Pass B).
2.  **Lookup** the corresponding speaker in the **Diarization Map** (from Pass A) using timestamp overlap.
3.  **Result:** A transcript that says: `Speaker A: "I go-ed to the store um yesterday"` (Diarized + Raw).

---

## 2. Streaming Audio
*   **Model:** `universal`
*   **Diarization:** No `speaker_labels` parameter (not supported in same way). Use `on_turn` events or channel separation if available.
*   **Rawness:** `punctuate=False` is generally supported in streaming if configured correctly, but less strict than Batch.

## 3. Troubleshooting
*   **"speaker_labels cannot be True when punctuate is set to False":** You tried to do it in one pass. **STOP.** Use the Dual-Pass Protocol.
*   **"Transcriber object has no attribute upload":** Use `transcriber.upload_file(path)`.
*   **"It's too slow":** We are running two transcriptions. It's the price of perfection. Upload is the bottleneck, and we optimized that (Upload Once).

---
*Verified by The Law. Any agent deviating from this spec is subject to immediate termination.*