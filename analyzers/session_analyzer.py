#!/usr/bin/env python3
"""
Comprehensive Session Analysis Engine (STUDENT-ONLY + LOCAL AI)
Analyzes ESL lesson transcripts for teaching insights using local, free tools.
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any
import sys
import logging

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    print("WARNING: textblob not found. Run 'pip install textblob' for advanced metrics.")
    TEXTBLOB_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class SessionAnalyzer:
    """Analyzes session data for ESL teaching insights"""

    def __init__(self, session_data: Dict[str, Any]):
        self.session = session_data
        self.turns = session_data.get('turns', [])

        # --- Find the Student ---
        self.speaker_map = session_data.get('speaker_map', {})
        self.teacher_name = session_data.get('teacher_name', 'Teacher')
        self.student_name = session_data.get('student_name', 'Student')

        self.student_label = 'Unknown'
        for label, name in self.speaker_map.items():
            if name == self.student_name:
                self.student_label = label
                break

        if self.student_label == 'Unknown':
            logger.warning("Could not find student label in speaker_map. Analysis may be empty.")
            self.student_turns = []
            self.student_full_text = ""
        else:
            logger.info(f"Analyzer: Found Student '{self.student_name}' with label '{self.student_label}'")
            self.student_turns = self._get_turns_for_speaker(self.student_label)
            # Create one giant text blob for the student, for TextBlob analysis
            self.student_full_text = " ".join([t['transcript'] for t in self.student_turns])


    def analyze_all(self) -> Dict[str, Any]:
        """Run all analyses for the STUDENT ONLY"""

        student_metrics = {
            'speaking_rate': self.analyze_speaking_rate(),
            'pauses': self.analyze_pauses(),
            'complexity_basic': self.analyze_complexity(), # Your original math
            'vocabulary_analysis': self.analyze_vocabulary(), # NEW: Lemma analysis
            'advanced_local_analysis': self.run_textblob_analysis(), # The new "smart" analysis
            'fillers': self.analyze_fillers(),
        }

        return {
            'session_info': self._get_session_info(),
            'student_metrics': student_metrics,
            'marked_turns': self._get_marked_turns_summary(),
            'action_items': self._get_action_items()
            # We will add 'lemur_analysis' in the lemur_query.py script
        }

    def _get_session_info(self) -> Dict[str, Any]:
        """Basic session information"""
        return {
            'session_id': self.session.get('session_id'),
            'teacher_name': self.teacher_name,
            'student_name': self.student_name,
            'start_time': self.session.get('start_time'),
            'end_time': self.session.get('end_time'),
            'total_turns_student': len(self.student_turns),
            'speaker_map': self.speaker_map
        }

    def _get_turns_for_speaker(self, speaker_label: str) -> List[Dict[str, Any]]:
        """Helper to filter turns for a specific speaker label"""
        if speaker_label == 'Unknown': return []
        return [t for t in self.turns if t.get('speaker') == speaker_label]

    # --- NEW: Free, Local, "Smart" Analysis ---
    def run_textblob_analysis(self) -> Dict[str, Any]:
        """
        Runs TextBlob analysis on the student's full text.
        This is the "free" open-source analysis you wanted.
        """
        if not TEXTBLOB_AVAILABLE or not self.student_full_text:
            return {'error': 'TextBlob not available or no student text.'}

        try:
            blob = TextBlob(self.student_full_text)

            # 1. Polarity: How positive/negative (range -1.0 to 1.0)
            polarity = round(blob.sentiment.polarity, 2)

            # 2. Subjectivity: How opinionated (range 0.0 to 1.0)
            subjectivity = round(blob.sentiment.subjectivity, 2)

            # 3. Noun Phrases: Find key topics
            # We find the top 5 most frequent topics they discussed
            noun_phrases = [str(p) for p in blob.noun_phrases if len(p) > 1]
            top_noun_phrases = dict(Counter(noun_phrases).most_common(5))

            return {
                'sentiment_polarity': polarity,
                'sentiment_subjectivity': subjectivity,
                'top_noun_phrases': top_noun_phrases,
                'polarity_assessment': self._assess_polarity(polarity),
                'subjectivity_assessment': self._assess_subjectivity(subjectivity)
            }
        except Exception as e:
            logger.error(f"TextBlob analysis failed: {e}")
            return {'error': str(e)}

    def _assess_polarity(self, score: float) -> str:
        if score > 0.3: return "Very Positive"
        if score > 0.1: return "Positive"
        if score < -0.3: return "Very Negative"
        if score < -0.1: return "Negative"
        return "Neutral"

    def _assess_subjectivity(self, score: float) -> str:
        if score > 0.7: return "Very Opinionated"
        if score > 0.4: return "Opinionated"
        return "Objective"
    # --- END NEW ---

    # --- "Fast & Free" Math-Based Metrics (Quantifiable) ---
    def analyze_speaking_rate(self) -> Dict[str, Any]:
        """Analyze words per minute over time for the student"""
        rates = []
        for turn in self.student_turns:
            wpm = turn.get('analysis', {}).get('speaking_rate_wpm')
            if wpm:
                rates.append({'turn_order': turn['turn_order'], 'wpm': wpm})
        if not rates: return {'error': 'No speaking rate data'}

        wpms = [r['wpm'] for r in rates]
        avg_wpm = sum(wpms) / len(wpms)
        return {
            'average_wpm': round(avg_wpm, 1),
            'min_wpm': round(min(wpms), 1),
            'max_wpm': round(max(wpms), 1)
        }

    def analyze_pauses(self) -> Dict[str, Any]:
        """Analyze pause patterns for the student"""
        all_pauses, long_pauses = [], []
        for turn in self.student_turns:
            pauses = turn.get('analysis', {}).get('pauses', [])
            for pause in pauses:
                all_pauses.append(pause['duration_ms'])
                if pause['duration_ms'] > 1000:
                    long_pauses.append(pause['duration_ms'])

        if not all_pauses: return {'message': 'No pause data'}

        return {
            'total_pauses': len(all_pauses),
            'long_pauses_gt_1s': len(long_pauses),
            'average_pause_ms': round(sum(all_pauses) / len(all_pauses), 1),
            'total_pause_time_ms': sum(all_pauses)
        }

    def analyze_complexity(self) -> Dict[str, Any]:
        """Analyze vocabulary complexity for the student"""
        all_words = []
        for turn in self.student_turns:
            words = turn.get('words', [])
            all_words.extend([w['text'].lower() for w in words])

        if not all_words:
            return {'error': 'No word data', 'total_words': 0}

        unique_words = set(all_words)
        return {
            'total_words': len(all_words),
            'unique_words': len(unique_words),
            'vocabulary_diversity': round(len(unique_words) / len(all_words), 3) if all_words else 0,
        }

    def analyze_fillers(self) -> Dict[str, Any]:
        """Count filler words for the student"""
        fillers = ['um', 'uh', 'like', 'you know', 'so', 'well', 'actually']
        filler_counts = Counter()
        for turn in self.student_turns:
            text = turn['transcript'].lower()
            for filler in fillers:
                count = len(re.findall(r'\b' + filler + r'\b', text))
                if count > 0:
                    filler_counts[filler] += count

        total_fillers = sum(filler_counts.values())
        total_words = self.analyze_complexity().get('total_words', 0) # Relies on complexity

        return {
            'total_fillers': total_fillers,
            'filler_percentage': round(total_fillers / total_words * 100, 2) if total_words > 0 else 0,
            'by_type': dict(filler_counts.most_common(5)),
        }

    def analyze_vocabulary(self) -> Dict[str, Any]:
        """Analyze vocabulary using lemmas for all speakers."""
        if not TEXTBLOB_AVAILABLE:
            return {'error': 'TextBlob not available. Cannot perform vocabulary analysis.'}

        teacher_label = None
        for label, name in self.speaker_map.items():
            if name == self.teacher_name:
                teacher_label = label
                break
        
        if not teacher_label:
            logger.warning("Could not find teacher label in speaker_map.")

        student_words = []
        for turn in self.student_turns:
            student_words.extend([w['text'].lower() for w in turn.get('words', [])])

        teacher_words = []
        if teacher_label:
            teacher_turns = self._get_turns_for_speaker(teacher_label)
            for turn in teacher_turns:
                teacher_words.extend([w['text'].lower() for w in turn.get('words', [])])

        student_lemmas = {TextBlob(word).words[0].lemmatize() for word in student_words if word.isalpha()}
        teacher_lemmas = {TextBlob(word).words[0].lemmatize() for word in teacher_words if word.isalpha()}
        
        combined_lemmas = student_lemmas.union(teacher_lemmas)

        return {
            'student_unique_lemmas': len(student_lemmas),
            'teacher_unique_lemmas': len(teacher_lemmas),
            'combined_unique_lemmas': len(combined_lemmas),
            'student_teacher_lemma_overlap': len(student_lemmas.intersection(teacher_lemmas)),
        }

    # --- Session-Wide (Mixed) Data ---
    def _get_marked_turns_summary(self) -> Dict[str, Any]:
        """Summary of marked turns (all speakers)"""
        marked = [t for t in self.turns if t.get('marked', False)]
        return {
            'total_marked': len(marked),
            'marked_turns': [{
                'turn_order': t['turn_order'],
                'speaker': self.speaker_map.get(t.get('speaker'), t.get('speaker')),
                'mark_type': t.get('mark_type'),
                'transcript': t['transcript']
            } for t in marked]
        }

    def _get_action_items(self) -> Dict[str, Any]:
        """Extract action items (all speakers)"""
        action_items_raw = self.session.get('action_items', [])
        action_items_named = [
            {
                "turn_order": item.get('turn_order'),
                "speaker": self.speaker_map.get(item.get('speaker'), item.get('speaker')),
                "transcript": item.get('transcript')
            } for item in action_items_raw
        ]
        return {
            "total_action_items": len(action_items_named),
            "action_items": action_items_named
        }

# --- Main execution ---
def analyze_session_file(session_file: Path) -> Dict[str, Any]:
    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load session file: {session_file}. Error: {e}")
        sys.exit(1)

    analyzer = SessionAnalyzer(session_data)
    return analyzer.analyze_all()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python session_analyzer.py <session_file.json>")
        print("This script is now called automatically by main.py")
        sys.exit(1)

    session_file = Path(sys.argv[1])
    logger.info(f"--- Running Fast & Free Analysis on {session_file.name} ---")
    results = analyze_session_file(session_file)

    # Save analysis to session_..._analysis.json
    output_file = session_file.parent / f"{session_file.stem}_analysis.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ (Free) Analysis saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save analysis file: {output_file}. Error: {e}")
        sys.exit(1)
