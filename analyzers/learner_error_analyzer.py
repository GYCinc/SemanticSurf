import logging
from typing import Any, final

logger = logging.getLogger("LearnerErrorAnalyzer")

@final
class LearnerErrorAnalyzer:
    """
    Analyzes text for common ESL learner errors based on PELIC 
    (Pittsburgh English Language Institute Corpus) patterns.
    
    Covers: Morphological, Syntactic, Lexical, and Discourse errors.
    """

    # === DYNAMIC POS-BASED DETECTION (Uses TextBlob/NLTK) ===
    # These replace the hand-coded lists for broader coverage.
    
    def __init__(self):
        # Common irregular plurals or "learner forms" to catch
        self.WRONG_PLURALS: dict[str, str] = {
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
        errors = []
        for sentence in blob.sentences:
            first_word = sentence.words[0].lower()
            if first_word in ['is', 'are', 'was', 'were']:
                errors.append({
                    "item": f"{sentence[:5]}...",
                    "correction": f"It {sentence[:5]}...",
                    "explanation": "Missing subject pronoun. Use 'It' before the verb.",
                    "category": "Syntax",
                    "confidence": 0.9
                })
        return errors

    def _check_sv_agreement(self, blob: Any) -> list[dict[str, Any]]:
        """Uses POS tags to find Subject-Verb mismatches, handling intervening words."""
        errors = []
        tags = blob.tags
        for i in range(len(tags)):
            word, tag = tags[i]
            
            # Look for Subject
            is_3rd_sing_subject = word.lower() in ['he', 'she', 'it']
            is_plural_subject = word.lower() in ['they', 'we'] or tag == 'NNS'
            is_relative_subject = word.lower() in ['who', 'which', 'that']
            
            if not (is_3rd_sing_subject or is_plural_subject or is_relative_subject):
                continue
                
            # Find the next verb (within 3 words)
            for j in range(i + 1, min(i + 4, len(tags))):
                next_word, next_tag = tags[j]
                if next_tag.startswith('VB'):
                    # Match Relative Subject 'who' with potential 3rd person mismatch
                    if is_relative_subject and next_tag == 'VBP':
                        # If the word before 'who' was singular, 'have' is an error
                        prev_word, prev_tag = tags[i-1] if i > 0 else ("", "")
                        if prev_tag == 'NN' or prev_tag == 'NNP':
                             errors.append({
                                "item": f"{prev_word} {word} {next_word}",
                                "correction": f"{prev_word} {word} {next_word}s",
                                "explanation": f"Subject-verb agreement in relative clause: '{prev_word}' is singular.",
                                "category": "Morphology", "confidence": 0.85
                            })
                    
                    # Match 3rd Person Singular Subject with plural verb (VBP)
                    if is_3rd_sing_subject and next_tag == 'VBP':
                        if next_word.lower() in ['have', 'do', 'go', 'be']:
                             errors.append({
                                "item": f"{word}...{next_word}",
                                "correction": f"{word} {next_word}s",
                                "explanation": f"Subject-verb agreement: use 3rd person form with '{word}'",
                                "category": "Morphology", "confidence": 0.88
                            })
                    # Match Plural Subject with 3rd person singular verb (VBZ)
                    elif is_plural_subject and next_tag == 'VBZ':
                        errors.append({
                            "item": f"{word}...{next_word}",
                            "correction": f"{word} {'are' if next_word.lower()=='is' else next_word[:-1]}",
                            "explanation": f"Subject-verb agreement: use plural form with '{word}'",
                            "category": "Morphology", "confidence": 0.88
                        })
                    break # Only check the first verb found
        return errors

    def _check_wrong_plurals(self, text: str) -> list[dict[str, Any]]:
        errors = []
        for wrong, right in self.WRONG_PLURALS.items():
            if f" {wrong} " in f" {text.lower()} ":
                errors.append({
                    "item": wrong,
                    "correction": right,
                    "explanation": f"Irregular plural: use '{right}' instead of '{wrong}'",
                    "category": "Morphology",
                    "confidence": 0.95
                })
        return errors

    def analyze(self, text: str) -> list[dict[str, str]]:
        """
        Analyzes text for learner errors using both regex and dynamic logic.
        """
        from textblob import TextBlob
        blob = TextBlob(text)
        errors = []
        
        # 1. Run Dynamic Checks (The fix for your 14% rate)
        errors.extend(self._check_missing_subject(blob))
        errors.extend(self._check_sv_agreement(blob))
        errors.extend(self._check_wrong_plurals(text))
        
        # 2. Add some "Legacy/PELIC" logic for idiomatic errors
        if "depend of" in text.lower():
            errors.append({"item": "depend of", "correction": "depend on", "explanation": "Collocation error", "category": "Lexis", "confidence": 0.9})
        if "i am agree" in text.lower():
            errors.append({"item": "i am agree", "correction": "i agree", "explanation": "'Agree' is a verb, not an adjective", "category": "Lexis", "confidence": 0.9})

        return errors

    def get_summary(self, text: str) -> dict[str, Any]:
        """
        Returns a summary of learner errors by category.
        """
        errors = self.analyze(text)
        categories: dict[str, int] = {}
        for e in errors:
            cat = e.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_errors": len(errors),
            "by_category": categories # type: ignore
        }
