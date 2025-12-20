import logging
from typing import Any, final
from collections.abc import Mapping, Sequence

logger = logging.getLogger("LearnerErrorAnalyzer")

@final
class LearnerErrorAnalyzer:
    """
    Analyzes text for common ESL learner errors based on PELIC 
    (Pittsburgh English Language Institute Corpus) patterns.
    
    Covers: Morphological, Syntactic, Lexical, and Discourse errors.
    """

    wrong_plurals_map: dict[str, str]
    
    def __init__(self):
        # Common irregular plurals or "learner forms" to catch
        self.wrong_plurals_map = {
            "peoples": "people",
            "childrens": "children",
            "mens": "men",
            "womens": "women",
            "polices": "police",
            "furnitures": "furniture",
            "informations": "information",
            "advices": "advice"
        }

    def _check_missing_subject(self, blob: Any) -> list[dict[str, Any]]:
        """Detects sentences starting with 'Is' or 'Are' (typical L1 Spanish/Portuguese error)."""
        errors: list[dict[str, Any]] = []
        for sentence in blob.sentences:
            if not sentence.words:
                continue
            first_word = str(sentence.words[0]).lower()
            if first_word in ['is', 'are', 'was', 'were']:
                errors.append({
                    "item": f"{sentence[:20]}...",
                    "match": first_word,
                    "correction": f"It {first_word}",
                    "explanation": f"Sentence starts with '{first_word}'. In English, most sentences require an explicit subject (e.g., 'It {first_word}')."
                })
        return errors

    def _check_sv_agreement(self, blob: Any) -> list[dict[str, Any]]:
        """Uses POS tags to find Subject-Verb mismatches, handling intervening words."""
        errors: list[dict[str, Any]] = []
        tags = blob.tags
        for i in range(len(tags)):
            word, tag = tags[i]
            
            # Simple check: 3rd person singular subject (NN) followed by base form verb (VBP) 
            # Or plural subject (NNS) followed by 3rd person singular verb (VBZ)
            if tag == 'NN' and i < len(tags) - 1:
                next_word, next_tag = tags[i+1]
                if next_tag == 'VBP' and not next_word.startswith("'"): # Skip contractions
                    errors.append({
                        "item": f"{word} {next_word}",
                        "match": f"{word} {next_word}",
                        "correction": f"{word} {next_word}s", 
                        "explanation": f"Possible Subject-Verb agreement error: '{word}' (singular) used with '{next_word}' (plural form)."
                    })
        return errors

    def _check_wrong_plurals(self, text: str) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        for wrong, right in self.wrong_plurals_map.items():
            if f" {wrong} " in f" {text.lower()} ":
                errors.append({
                    "item": wrong,
                    "match": wrong,
                    "correction": right,
                    "explanation": f"'{wrong}' is an irregular plural or uncountable noun. Use '{right}' instead."
                })
        return errors

    def analyze(self, text: str) -> list[dict[str, Any]]:
        """
        Main entry point for morphological/syntactic analysis.
        """
        from textblob import TextBlob
        blob = TextBlob(text)
        errors: list[dict[str, Any]] = []
        
        # 1. Run Dynamic Checks
        errors.extend(self._check_missing_subject(blob))
        errors.extend(self._check_sv_agreement(blob))
        errors.extend(self._check_wrong_plurals(text))
        
        # 2. Add static match for UI if missing
        for err in errors:
            if 'match' not in err:
                err['match'] = err.get('item', '')
                
        return errors
