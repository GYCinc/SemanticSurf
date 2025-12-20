import re
import logging
from typing import final

logger = logging.getLogger("ArticleAnalyzer")

@final
class ArticleAnalyzer:
    """
    Analyzes text specifically for Indefinite Article errors (a vs an).
    """

    vowels: set[str]
    an_exceptions: list[str]
    a_exceptions: list[str]

    def __init__(self):
        # Identify vowel sounds (simplified for MVP)
        self.vowels = set("aeiou")
        # Exceptions could be loaded here (e.g., "hour", "umbrella", "university")
        self.an_exceptions = ["hour", "honest", "heir", "honor"] # Words starting with H but vowel sound
        self.a_exceptions = ["university", "united", "unique", "useful", "usage", "eu", "one"] # Vowel start but consonant sound

    def analyze(self, text: str) -> list[dict[str, str]]:
        """
        Analyzes text specifically for Indefinite Article errors (a vs an).
        """
        errors: list[dict[str, str]] = []
        
        # Regex to find "a [word]" or "an [word]" case-insensitive
        # \b ensures word boundary
        matches = re.finditer(r"\b(a|an)\s+(\w+)\b", text, re.IGNORECASE)
        
        for match in matches:
            article = match.group(1).lower()
            next_word = match.group(2).lower()
            
            # Logic for 'a' vs 'an'
            needs_an = self._starts_with_vowel_sound(next_word)
            
            if article == "a" and needs_an:
                errors.append({
                    "item": f"{article} {next_word}",
                    "match": f"{article} {next_word}",
                    "correction": f"an {next_word}",
                    "explanation": f"Use 'an' before '{next_word}' because it starts with a vowel sound."
                })
            elif article == "an" and not needs_an:
                errors.append({
                    "item": f"{article} {next_word}",
                    "match": f"{article} {next_word}",
                    "correction": f"a {next_word}",
                    "explanation": f"Use 'a' before '{next_word}' because it starts with a consonant sound."
                })
                
        return errors

    def _starts_with_vowel_sound(self, word: str) -> bool:
        """
        Determines if a word starts with a vowel sound.
        """
        if not word: return False
        
        # Specific exceptions
        if word in self.an_exceptions:
            return True
        if any(word.startswith(exc) for exc in self.a_exceptions):
            return False
            
        # Default rule: starts with vowel char
        return word[0] in self.vowels
