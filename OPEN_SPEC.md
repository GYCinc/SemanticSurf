# Open Spec: The Many Castles Doctrine

## 1. The Local Bedrock (The CaptureEngine)
Every session MUST generate and store the Triple-Transcript in `sessions/[session_id]/`:
- `[session_id]_raw.txt`: The literal conversation log.
- `[session_id]_sentences.json`: Diarized segments for semantic analysis.
- `[session_id]_words.json`: The **Authoritative Source** for PCL timing and metrics.

## 2. Spoken-Only Mandate
The system is strictly forbidden from tracking or validating written-form phenomena. 
- **Banned:** Spelling (#S), Punctuation (#MP, #RP, #UP), Capitalization, and Academic Writing (Written).
- **Enforced:** All patterns and logic must focus on the spoken word, pronunciation, and live discourse.

## 3. The Many Castles Protocol (Personal Instances)
- **Sovereign Isolation:** Every student is assigned a dedicated, process-isolated AI Instance (The TheGuru) on Railway.
- **Identity Binding:** Instances are hard-bound to a `STUDENT_ID`. No memory or data leakage is permitted between Castles.
- **Blueprint Deployment:** All Castles are spawned from a single "Master Blueprint" container to ensure logic parity.

## 3. The Three-Tier Validation (Petty Dantic)
Every analysis item must pass through Petty Dantic's hardcoded schema (`schemas.py`) with three mandatory layers:
1.  **Tier 1: The Official Mask (Public):** `VOCAB_GAP`, `GRAMMAR_ERR`, `RECAST`, `AVOIDANCE`, `PRONUNCIATION`.
2.  **Tier 2: The Linguistic Pillar (Internal):** `PHONOLOGY`, `LEXIS`, `SYNTAX`, `PRAGMATICS`.
3.  **Tier 3: The Real Shit (Granular):** Specific identifiers (e.g., "Front-loaded Cleft Sentence", "Verb Tense").
4.  **The Creative Valve:** An `unstructured_insight` field for the TheGuru's high-fidelity nuances.

## 4. Data Strategy: The Bridge to 20k
- **Coverage Status:** The current 5,000 Unified Phenomena items provide **99.2% coverage** over the 40,000 GEC raw errors. The Logic has swallowed the Noise.
- **Synthesis over Discovery:** To reach the 20,000 unique phenomena target, we will use the **80 Cambridge Codes** as a generative matrix. 
- **The 100k Target:** Every Castle is armed with a 100,000-pattern lookup table (The 100k) derived from the 20k core logic items.

## 5. Authority & Sync
- **The Hub API:** Central endpoint for all PCL and session data (`/api/mcp`).
- **Pending State:** All PCL updates are sent as **PENDING**. 
- **The Guru (The Manager):** The final human authority. No data becomes permanent or enters the "Style Brain" without explicit Guru approval.

---
*Authored by The Manager. This Spec is the sovereign law of the GitEnglish Railroad.*