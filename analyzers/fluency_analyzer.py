import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger("FluencyAnalyzer")

class FluencyAnalyzer:
    """
    Precision Timing Engine.
    Analyzes millisecond-level word data to identify hesitation patterns.
    Anchored in [session_id]_words.json.
    """

    def __init__(self, pause_threshold_ms: int = 300):
        self.pause_threshold = pause_threshold_ms

    def analyze_hesitation(self, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates statistical hesitation before words.
        Returns a list of 'Difficulty Targets' where the student struggled.
        """
        hesitations = []
        total_pause_time = 0
        
        for i in range(1, len(words)):
            current = words[i]
            prev = words[i-1]
            
            # AssemblyAI provides 'start' and 'end' in ms
            gap = current.get("start", 0) - prev.get("end", 0)
            
            if gap > self.pause_threshold:
                hesitations.append({
                    "word": current.get("text"),
                    "pre_word_gap_ms": gap,
                    "timestamp_ms": current.get("start"),
                    "speaker": current.get("speaker")
                })
                total_pause_time += gap

        return {
            "struggle_points": hesitations,
            "total_pause_ms": total_pause_time,
            "hesitation_count": len(hesitations),
            "avg_gap_ms": total_pause_time / len(hesitations) if hesitations else 0
        }

    def calculate_articulation_rate(self, words: List[Dict[str, Any]]) -> float:
        """Calculates WPM (Words Per Minute) excluding long silence."""
        if not words: return 0.0
        
        duration_ms = words[-1].get("end", 0) - words[0].get("start", 0)
        if duration_ms == 0: return 0.0
        
        # (Total words / duration in minutes)
        return (len(words) / (duration_ms / 60000))

    def compare_to_native(self, student_words: List[Dict[str, Any]], tutor_words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        The TRUE Naturalness Score.
        Compares the student's timing metrics against the tutor's native baseline.
        """
        s_rate = self.calculate_articulation_rate(student_words)
        t_rate = self.calculate_articulation_rate(tutor_words)
        
        return {
            "student_wpm": round(s_rate, 2),
            "tutor_wpm": round(t_rate, 2),
            "fluency_ratio": round(s_rate / t_rate, 2) if t_rate > 0 else 0,
            "naturalness_delta": round(t_rate - s_rate, 2)
        }
