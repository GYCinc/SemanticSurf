import logging
import re

logger = logging.getLogger("PrepositionAnalyzer")

class PrepositionAnalyzer:
    """
    Analyzes text for common preposition errors made by ESL learners.
    Based on PASTRIE (Preposition Annotation for Semantic Tagging of Resource Interoperability Efforts).
    """

    # Common preposition errors by category
    # Format: { "incorrect pattern": ("correction", "explanation") }
    COMMON_ERRORS: dict[str, tuple[str, str]] = {
        # Time prepositions
        "in the morning": ("in the morning", "CORRECT"),  # baseline
        "at the morning": ("in the morning", "Use 'in' with morning/afternoon/evening"),
        "on the morning": ("in the morning", "Use 'in' with morning/afternoon/evening"),
        "in night": ("at night", "Use 'at' with 'night'"),
        "on night": ("at night", "Use 'at' with 'night'"),
        
        # Location prepositions
        "arrive to": ("arrive at/in", "Use 'arrive at' (specific place) or 'arrive in' (city/country)"),
        "arrive on": ("arrive at/in", "Use 'arrive at' (specific place) or 'arrive in' (city/country)"),
        "enter to": ("enter", "'Enter' doesn't take a preposition"),
        "enter in": ("enter", "'Enter' doesn't take a preposition"),
        "go to home": ("go home", "'Home' doesn't need 'to' after 'go'"),
        "come to home": ("come home", "'Home' doesn't need 'to' after 'come'"),
        "return back": ("return", "'Return' already means 'go back'"),
        
        # Verb + Preposition collocations
        "depend of": ("depend on", "Use 'depend on'"),
        "interested for": ("interested in", "Use 'interested in'"),
        "afraid from": ("afraid of", "Use 'afraid of'"),
        "married with": ("married to", "Use 'married to'"),
        "different of": ("different from", "Use 'different from'"),
        "listen the": ("listen to the", "Use 'listen to'"),
        "explain me": ("explain to me", "Use 'explain to'"),
        "discuss about": ("discuss", "'Discuss' doesn't need 'about'"),
        "emphasize on": ("emphasize", "'Emphasize' doesn't need 'on'"),
        
        # Other common errors
        "in the weekend": ("on the weekend", "Use 'on' with weekend"),
        "at the weekend": ("on the weekend", "Use 'on' with weekend (American English)"),
        "in friday": ("on friday", "Use 'on' with days of the week"),
        "in monday": ("on monday", "Use 'on' with days of the week"),
        "in tuesday": ("on tuesday", "Use 'on' with days of the week"),
        "in my opinion to": ("in my opinion", "No preposition needed after 'in my opinion'"),
        "according with": ("according to", "Use 'according to'"),
    }

    def __init__(self):
        pass

    def analyze(self, text: str) -> list[dict[str, str]]:
        """
        Analyzes text for preposition errors.
        Returns a list of detected errors with corrections.
        """
        errors = []
        text_lower = text.lower()
        
        for pattern, (correction, explanation) in self.COMMON_ERRORS.items():
            if correction == "CORRECT":
                continue  # Skip baseline patterns
            if pattern in text_lower:
                errors.append({
                    "item": pattern,
                    "correction": correction,
                    "explanation": explanation,
                    "category": "Preposition"
                })
        
        return errors

    def get_summary(self, text: str) -> dict[str, int]:
        """
        Returns a summary of preposition errors found.
        """
        errors = self.analyze(text)
        return {
            "total_errors": len(errors),
            "unique_patterns": len(set(e["item"] for e in errors)),
        }
