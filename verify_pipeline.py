import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime

# Import the hardened components
from main import analyze_session_file, get_student_id
from analyzers.pos_analyzer import POSAnalyzer
from analyzers.ngram_analyzer import NgramAnalyzer
from analyzers.verb_analyzer import VerbAnalyzer
from analyzers.article_analyzer import ArticleAnalyzer
from analyzers.amalgum_analyzer import AmalgumAnalyzer
from analyzers.comparative_analyzer import ComparativeAnalyzer
from analyzers.phenomena_matcher import PhenomenaPatternMatcher

def run_deep_audit():
    print("\n" + "█"*60)
    print("🔬 DEEP-TISSUE PIPELINE AUDIT: LARGE DATASET VERIFICATION")
    print("█"*60 + "\n")

    # 1. THE DATASET (Realistic multi-turn session)
    session_data = {
        "session_id": "audit_test_999",
        "student_name": "Jocelyn",
        "teacher_name": "Aaron",
        "speaker_map": {"A": "Aaron", "B": "Jocelyn"},
        "start_time": datetime.now().isoformat(),
        "notes": "Jocelyn was energetic but struggled with past tense and 'the/a' usage in long sentences.",
        "turns": [
            {"speaker": "A", "transcript": "Hi Jocelyn! How was your weekend? Did you do anything fun?", "turn_order": 1},
            {"speaker": "B", "transcript": "My weekend is good. I go to park with my friend. We see a apple tree.", "turn_order": 2, "analysis": {"speaking_rate_wpm": 95}},
            {"speaker": "A", "transcript": "Oh, a park? That sounds lovely. Was it a big park?", "turn_order": 3},
            {"speaker": "B", "transcript": "Yes, it is very big. But I have been lived in city for long time so I like nature.", "turn_order": 4, "analysis": {"speaking_rate_wpm": 80}},
            {"speaker": "A", "transcript": "I agree. Nature is peaceful. In conclusion, we should enjoy the outdoors more often.", "turn_order": 5},
            {"speaker": "B", "transcript": "He don't like park. He prefer stay at home and play game.", "turn_order": 6, "analysis": {"speaking_rate_wpm": 110}},
            {"speaker": "A", "transcript": "That's a shame. Playing games is fun, but fresh air is important for health.", "turn_order": 7},
            {"speaker": "B", "transcript": "I think so. I will went again next week. I need to practice my English more, actually.", "turn_order": 8, "analysis": {"speaking_rate_wpm": 105}}
        ]
    }

    # 2. THE PIPELINE EXECUTION (Simulating upload_analysis_to_supabase)
    student_turns = [t for t in session_data["turns"] if t["speaker"] == "B"]
    tutor_turns = [t for t in session_data["turns"] if t["speaker"] == "A"]
    
    student_text = " ".join([t["transcript"] for t in student_turns])
    tutor_text = " ".join([t["transcript"] for t in tutor_turns])

    print(f"📊 Dataset Size: {len(session_data['turns'])} turns, {len(student_text.split())} student words.")

    # Execute Analysis
    start_total = time.time()
    
    # POS
    pos_counts = POSAnalyzer().analyze(student_text)
    pos_ratios = POSAnalyzer().get_ratios(student_text)
    
    # N-grams
    ngram_data = NgramAnalyzer().analyze(student_text)
    tutor_bigrams_raw = NgramAnalyzer().get_bigrams(tutor_text)
    print(f"DEBUG: Tutor Bigrams Sample: {tutor_bigrams_raw[:10]}")
    
    # Verbs & Articles
    verb_data = VerbAnalyzer().analyze(student_text)
    article_data = ArticleAnalyzer().analyze(student_text)
    
    # Comparative
    tutor_pos = POSAnalyzer().analyze(tutor_text)
    tutor_ngram = NgramAnalyzer().analyze(tutor_text)
    comp_data = ComparativeAnalyzer().compare(
        student_data={"pos": pos_counts, "ngrams": ngram_data, "text": student_text},
        tutor_data={"pos": tutor_pos, "ngrams": tutor_ngram, "text": tutor_text}
    )
    
    # Phenomena
    pm = PhenomenaPatternMatcher()
    pattern_matches = pm.match(student_text)
    
    end_total = time.time()

    # 3. THE CRITICAL EVALUATION
    print("\n" + "-"*40)
    print("📈 OUTPUT EVALUATION")
    print("-"*40)

    # Validate Naturalness
    s_nat = ngram_data['naturalness_score']
    t_nat = tutor_ngram['naturalness_score']
    print(f"Naturalness -> Student: {s_nat} | Tutor: {t_nat}")
    if t_nat > s_nat:
        print("✅ SUCCESS: Tutor correctly identified as more natural.")
    else:
        print("❌ DEVIATION: Tutor naturalness not significantly higher.")

    # Validate Overlap
    overlap = comp_data['comparison']['tutor_overlap_pct']
    print(f"Tutor Overlap: {overlap}%")
    
    # Validate Errors
    detected = []
    detected.extend([e['match'] for e in article_data.get('errors', [])])
    detected.extend([e['verb'] for e in verb_data.get('irregular_errors', [])])
    
    print(f"Detected Errors: {detected}")
    if "a apple" in str(detected):
        print("✅ SUCCESS: Article error 'a apple' captured.")
    else:
        print("❌ DEVIATION: Failed to catch 'a apple'.")

    # Validate POS Ratios
    v_ratio = pos_ratios['verb_ratio']
    print(f"Student Verb Ratio: {v_ratio}")
    if 0.1 < v_ratio < 0.4:
        print("✅ SUCCESS: Verb ratio within realistic conversational range.")
    else:
        print(f"❌ ANOMALY: Verb ratio {v_ratio} seems unrealistic.")

    print(f"\n⏱️ Total Execution Time: {round(end_total - start_total, 3)}s")
    
    print("\n" + "█"*60)
    print("🏁 AUDIT COMPLETE")
    print("█"*60 + "\n")

if __name__ == "__main__":
    run_deep_audit()