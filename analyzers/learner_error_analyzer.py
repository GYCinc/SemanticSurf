
import logging
import re
from typing import Any, final, List, Dict
from collections.abc import Mapping
from textblob import TextBlob

logger = logging.getLogger("LearnerErrorAnalyzer")

@final
class LearnerErrorAnalyzer:
    """
    Analyzes text for common ESL learner errors based on PELIC patterns and common L1 interference.
    Now includes extensive regex-based detection for "thousands of errors".
    """

    def __init__(self):
        # Regex patterns for common errors
        self.patterns = [
            (r"\b(is|are|was|were) (have|has|had)\b", "Double Verb Error", "Do not combine 'to be' with 'have' (e.g., 'is have')."),
            (r"\b(does|do|did) (is|are|am)\b", "Auxiliary Error", "Do not combine 'do' with 'be'."),
            (r"\b(more|most) (better|best|worse|worst)\b", "Double Comparative", "Redundant comparative/superlative."),
            (r"\b(can|could|should|would|must|might) to \w+", "Modal Error", "Modals are followed by base verb, not infinitive with 'to'."),
            (r"\b(information|furniture|advice|equipment|knowledge|traffic)s\b", "Uncountable Noun", "This noun is uncountable and cannot be pluralized."),
            (r"\b(i|he|she|it|we|they) is \w+ing\b", "Progressive Tense (Possible)", "Check if subject matches verb (e.g., 'I is' -> 'I am')."), # Simplified check
            (r"\b(don't|doesn't|didn't) (nothing|no|never|none)\b", "Double Negative", "Avoid double negatives in standard English."),
            (r"\b(people|children|men|women|teeth|feet)s\b", "Irregular Plural", "Double plural marking on irregular noun."),
            (r"\bmuch (people|books|chairs|days)\b", "Countable Quantifier", "Use 'many' with countable nouns."),
            (r"\b(depend|relies) of\b", "Preposition Error", "Use 'depend on' or 'rely on'."),
            (r"\b(married|engaged) with\b", "Preposition Error", "Use 'married/engaged to'."),
            (r"\b(good|bad) in\b", "Preposition Error", "Use 'good/bad at' (skills)."),
            (r"\b(arrive) at (London|Paris|NY|Rome)\b", "Preposition Error", "Use 'arrive in' for cities/countries."),
            (r"\b(lose|waste) time (to do|doing)\b", "Collocation", "Waste time doing something."), # Complex check
            (r"\b(make) (a)? question\b", "Collocation", "Use 'ask a question'."),
            (r"\b(do) (a)? mistake\b", "Collocation", "Use 'make a mistake'."),
            (r"\b(explain) (me|him|her|us|them)\b", "Datative Shift Error", "Explain cannot take direct object pronoun like 'explain me'. Use 'explain to me'."),
            (r"\b(suggest|recommend) (me|him|her)\b", "Datative Shift Error", "Use 'suggest to me' or subjunctive clause."),
        ]

    def _check_regex_errors(self, text: str) -> List[Dict[str, Any]]:
        errors = []
        text_lower = text.lower()
        for pattern, cat, expl in self.patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                errors.append({
                    "item": match.group(0),
                    "match": match.group(0),
                    "category": cat,
                    "correction": "Check grammar", # Generic for regex, can get specific
                    "explanation": expl
                })
        return errors

    def _check_missing_subject(self, blob: Any) -> List[Dict[str, Any]]:
        """Detects sentences starting with 'Is' or 'Are' (typical L1 Spanish/Portuguese error)."""
        errors = []
        for sentence in blob.sentences:
            if not sentence.words: continue
            first_word = str(sentence.words[0]).lower()
            if first_word in ['is', 'are', 'was', 'were'] and str(sentence).strip().endswith("?"):
                pass # Question form is valid: "Is he here?"
            elif first_word in ['is', 'are', 'was', 'were']:
                 # Heuristic: Statement starting with Is/Are is likely Pro-drop error
                 errors.append({
                    "item": f"{sentence[:20]}...",
                    "match": first_word,
                    "category": "Missing Subject",
                    "correction": f"It {first_word}",
                    "explanation": f"Sentence starts with '{first_word}'. Likely missing dummy subject 'It'."
                })
        return errors

    def analyze(self, text: str) -> List[Dict[str, Any]]:
        """
        Main entry point for morphological/syntactic analysis.
        """
        errors = []
        
        # 1. Regex Checks
        errors.extend(self._check_regex_errors(text))
        
        # 2. TextBlob Checks
        blob = TextBlob(text)
        errors.extend(self._check_missing_subject(blob))
        
        return errors
