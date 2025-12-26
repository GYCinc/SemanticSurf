import os
import logging
from typing import Dict, List, Optional
import json

# Setup logging
logger = logging.getLogger("AmalgumAnalyzer")

class AmalgumAnalyzer:
    """
    Simulates the AMALGUM corpus analysis for register detection (Academic vs Conversational).
    
    Since the full AMALGUM corpus is large, this version bootstraps with a 
    seed dictionary of register-specific markers.
    """
    
    def __init__(self):
        self._load_seed_data()
        
    def _load_seed_data(self):
        """
        Loads a seed list of words/ngrams that are strongly associated 
        with either Academic or Conversational registers.
        """
        # In a full implementation, this would load from a large N-gram DB
        self.academic_markers = {
            "moreover": 0.8,
            "however": 0.6,
            "therefore": 0.8,
            "startlingly": 0.9,
            "consequently": 0.8,
            "in conclusion": 0.9,
            "according to": 0.7,
            "analysis": 0.6,
            "hypothesis": 0.7,
            "demonstrate": 0.6
        }
        
        self.conversational_markers = {
            "like": 0.5,
            "maybe": 0.4,
            "stuff": 0.7,
            "kind of": 0.6,
            "sort of": 0.6,
            "you know": 0.7,
            "basically": 0.5,
            "actually": 0.4,
            "pretty much": 0.6
        }
        logger.info("📚 AMALGUM Seed Data Loaded (Academic & Conversational markers)")

    def analyze_register(self, text: str) -> Dict[str, float]:
        """
        Analyzes the text and returns a 'register score' dictionary.
        High academic_score = more formal.
        High casual_score = more informal.
        """
        text_lower = text.lower()
        
        academic_score = 0.0
        casual_score = 0.0
        
        # Check markers
        for marker, weight in self.academic_markers.items():
            if marker in text_lower:
                academic_score += weight
                
        for marker, weight in self.conversational_markers.items():
            if marker in text_lower:
                casual_score += weight
                
        # Normalize roughly by length or just return raw scores for now
        # For this MVP, we just return the raw accumulation
        return {
            "academic": round(academic_score, 2),
            "conversational": round(casual_score, 2)
        }

    def get_genre_classification(self, text: str) -> str:
        """
        Returns 'Academic', 'Conversational', or 'Neutral' based on scores.
        """
        scores = self.analyze_register(text)
        aca = scores['academic']
        conv = scores['conversational']
        
        if aca > conv + 0.5:
            return "Academic"
        elif conv > aca + 0.5:
            return "Conversational"
        else:
            return "Neutral"

    def analyze(self, text: str) -> Dict[str, float]:
        """Standard interface alias."""
        return self.analyze_register(text)
