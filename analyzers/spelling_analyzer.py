
import os
import re
import nltk
from nltk.corpus import words
from textblob import TextBlob
import logging

logger = logging.getLogger(__name__)

class SpellingAnalyzer:
    def __init__(self):
        self._ensure_corpus()
        self.english_words = set(words.words())
        logger.info(f"Loaded {len(self.english_words)} words from NLTK corpus")

    def _ensure_corpus(self):
        try:
            nltk.data.find('corpora/words')
        except LookupError:
            logger.info("Downloading NLTK 'words' corpus...")
            nltk.download('words')

    def check_text(self, text: str):
        """
        Checks text for potential misspellings.
        Returns a list of dicts: {'word': str, 'position': int}
        """
        misspellings = []
        # Simple tokenization: split by space, remove punctuation
        # This mirrors the logic in NLP-Spell-Checker: re.sub(r"[^\w]", "", word.lower())
        
        # We want to preserve position, so we iterate carefully or just use regex to find words
        for match in re.finditer(r"\b\w+\b", text):
            word = match.group()
            # Skip numbers or excessively short/long things logic could go here
            if not word.isalpha():
                continue
                
            clean_word = word.lower()
            if clean_word not in self.english_words:
                # Basic heuristic: ignore proper nouns if capitalized? 
                # The repo didn't do this, it just checked lower().
                # But NLTK words contains names too.
                # If the word is capitalized in text but lowercase is not in dict, maybe it's a name?
                # For now, stick to the repo's logic: re.sub(..., word.lower())
                
                misspellings.append({
                    'word': word,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return misspellings

    def is_misspelled(self, word: str) -> bool:
        clean_word = re.sub(r"[^\w]", "", word.lower())
        if not clean_word:
            return False
        return clean_word not in self.english_words

    def suggest_correction(self, word: str) -> str:
        """
        Returns a suggested correction for a misspelled word using TextBlob.
        """
        w = TextBlob(word)
        return str(w.correct())
