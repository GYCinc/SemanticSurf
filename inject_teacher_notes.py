#!/usr/bin/env python3
"""
Teacher Note Injection Tool (The "Teacher's Red Pen")
-----------------------------------------------------
Scans for pending 'corpus_review' files in admin_inbox.
Allows the Teacher (User) to inject:
1. Session Notes / Global Feedback
2. Specific Corrections
3. Validated Lemma Additions

Outputs: 'teacher_injection.json' for the Classifier to consume.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, List, Dict

# Setup Paths
BASE_DIR = Path(__file__).resolve().parent
INBOX_DIR = BASE_DIR / "admin_inbox"
OUTPUT_DIR = BASE_DIR / "admin_outbox"

def load_pending_reviews() -> List[Path]:
    if not INBOX_DIR.exists():
        return []
    return list(INBOX_DIR.glob("corpus_review_*.json"))

def interactive_injection(review_path: Path):
    print(f"\n📝 Reviewing Session: {review_path.name}")
    try:
        with open(review_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    student = data.get('student_name', 'Unknown')
    print(f"   Student: {student}")
    print(f"   Transcript Snippet: \"{data.get('transcript_snippet', '')[:100]}...\"")
    print("-" * 50)

    # 1. Capture Global Feedback (The "Vibe")
    print("\n🎤 ENTER TEACHER NOTES (Global Feedback/Vibe):")
    print("(Press ENTER twice to finish)")
    notes_lines = []
    while True:
        line = input()
        if not line and notes_lines and not notes_lines[-1]: # Stop on empty line if we have content
             break
        if not line and not notes_lines: # Allow single empty enter to skip if lazy? No, enforce at least 'N/A'
             # actually lets just break on empty line
             break
        notes_lines.append(line)
    
    teacher_notes = "\n".join(notes_lines).strip()
    if not teacher_notes:
        teacher_notes = "Great effort today!" # Default fallback

    # 2. Capture Specific Corrections (The "Red Pen")
    corrections = []
    print("\n🖍️  Add Specific Corrections? (y/n)")
    if input().lower().startswith('y'):
        print("   Format: [Mistake] -> [Correction] (Type 'done' to finish)")
        while True:
            entry = input("   > ")
            if entry.lower() == 'done': break
            if "->" in entry:
                parts = entry.split("->")
                corrections.append({
                    "mistake": parts[0].strip(),
                    "correction": parts[1].strip()
                })
            else:
                print("   ⚠️  Please use 'Mistake -> Correction' format.")

    # 3. Approve/Reject Corpus Additions (Lemmas)
    approved_lemmas = []
    proposed = data.get('proposed_corpus_additions', [])
    if proposed:
        print(f"\n📚 Review {len(proposed)} Proposed Lemmas for Corpus:")
        # Simple bulk approval for MVP, or iterate?
        # Let's show top 10 and ask if all good
        print(f"   Top 5: {', '.join(str(p) for p in proposed[:5])}...")
        res = input("   Approve all? (y/n/edit): ").lower()
        if res == 'y':
            approved_lemmas = proposed
        elif res == 'edit':
             print("   Enter valid lemmas separated by comma:")
             manual = input("   > ")
             approved_lemmas = [w.strip() for w in manual.split(',') if w.strip()]
    
    # Construct Injection Payload
    injection_packet = {
        "session_id": data.get('session_id'),
        "student_name": student,
        "teacher_notes": teacher_notes,
        "manual_corrections": corrections,
        "approved_corpus_lemmas": approved_lemmas,
        "injection_timestamp": "Now",
        "status": "INJECTED"
    }

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"teacher_injection_{student}_{data.get('session_id', 'unknown')}.json"
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(injection_packet, f, indent=2)
    
    print(f"\n✅ Injection Saved: {out_file.name}")
    print("   Ready for Classifier!")

def main():
    print("="*60)
    print("   💉 ANTI-GRAVITY MANUAL INJECTION INTERFACE 💉")
    print("="*60)
    
    pending = load_pending_reviews()
    if not pending:
        print("📭 No pending corpus reviews found in 'admin_inbox'.")
        print("   (Run verify_session_generation.py or upload_audio_aai.py first)")
        sys.exit(0)

    print(f"Found {len(pending)} pending reviews.")
    for i, p in enumerate(pending):
        print(f"[{i+1}] {p.name}")
    
    choice = input("\nSelect # to inject notes (or 'q' to quit): ")
    if choice.lower() == 'q': return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(pending):
            interactive_injection(pending[idx])
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")

if __name__ == "__main__":
    main()
