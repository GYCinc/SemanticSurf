import json
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("StudentCorpusEngine")

class StudentCorpusEngine:
    """
    The engine for the Personal Language Corpus (PCL).
    Processes word-level timing and confidence data for Hub synchronization.
    Anchored in the authoritative transcripts.words data.
    """

    def __init__(self):
        # Basic stop words to keep the PCL focused on meaningful production
        self.ignore_list = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "i", "you", "he", "she", "it", "we", "they"}

    def extract_from_word_array(self, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes the authoritative word array to count every word produced.
        This is the BEDROCK of the Personal Language Corpus.
        """
        word_counts = {}
        for w in words:
            # AssemblyAI word objects have 'text', 'start', 'end', 'confidence', and 'speaker' (if diarized)
            # We ONLY count words where the speaker is NOT Aaron (the Tutor)
            if w.get("speaker") == "Aaron" or w.get("speaker") == "Tutor":
                continue
                
            text = w.get("text", "").lower().strip(".,?!\"'()[]")
            if not text or text in self.ignore_list:
                continue
                
            if text not in word_counts:
                word_counts[text] = {
                    "count": 0, 
                    "last_produced": datetime.now().isoformat(), # Fallback if no specific TS
                    "avg_confidence": 0.0,
                    "occurrences": []
                }
            
            word_counts[text]["count"] += 1
            word_counts[text]["occurrences"].append({
                "start_ms": w.get("start"),
                "end_ms": w.get("end"),
                "confidence": w.get("confidence")
            })
            
        # Final formatting for the Hub
        return {
            "words": [
                {
                    "word": k, 
                    "count": v["count"], 
                    "last_produced": v["last_produced"],
                    "confidence": sum(o["confidence"] for o in v["occurrences"]) / len(v["occurrences"]) if v["occurrences"] else 0
                } for k, v in word_counts.items()
            ],
            "total_production": sum(v["count"] for v in word_counts.values())
        }

    def prepare_hub_payload_from_words(self, student_name: str, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepares the payload for the /api/mcp/pcl/sync endpoint using the word array.
        """
        stats = self.extract_from_word_array(words)
        return {
            "student_name": student_name,
            "timestamp": datetime.now().isoformat(),
            "source": "authoritative_word_transcript",
            "pcl_stats": stats
        }

    def extract_production_stats(self, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Legacy turn-based extraction (kept for backward compatibility)."""
        word_counts = {}
        for turn in turns:
            if "Tutor" in turn.get("speaker", ""): continue
            words = turn.get("words", [])
            for w in words:
                text = w.get("text", "").lower().strip(".,?!")
                if not text or text in self.ignore_list: continue
                if text not in word_counts:
                    word_counts[text] = {"count": 0, "last_produced": turn.get("timestamp")}
                word_counts[text]["count"] += 1
        return {
            "words": [{"word": k, "count": v["count"], "last_produced": v["last_produced"]} for k, v in word_counts.items()],
            "total_production": sum(v["count"] for v in word_counts.values())
        }