import logging
from typing import Optional, Any

logger = logging.getLogger("POSAnalyzer")

class POSAnalyzer:
    """
    Performs Part-of-Speech tagging using TextBlob.
    Provides POS tag distribution and can flag unusual patterns.
    """

    # Penn Treebank Tag Descriptions (for reference)
    TAG_DESCRIPTIONS: dict[str, str] = {
        "CC": "Coordinating conjunction",
        "CD": "Cardinal number",
        "DT": "Determiner",
        "EX": "Existential there",
        "FW": "Foreign word",
        "IN": "Preposition/subordinating conjunction",
        "JJ": "Adjective",
        "JJR": "Adjective, comparative",
        "JJS": "Adjective, superlative",
        "LS": "List item marker",
        "MD": "Modal",
        "NN": "Noun, singular or mass",
        "NNS": "Noun, plural",
        "NNP": "Proper noun, singular",
        "NNPS": "Proper noun, plural",
        "PDT": "Predeterminer",
        "POS": "Possessive ending",
        "PRP": "Personal pronoun",
        "PRP$": "Possessive pronoun",
        "RB": "Adverb",
        "RBR": "Adverb, comparative",
        "RBS": "Adverb, superlative",
        "RP": "Particle",
        "SYM": "Symbol",
        "TO": "to",
        "UH": "Interjection",
        "VB": "Verb, base form",
        "VBD": "Verb, past tense",
        "VBG": "Verb, gerund/present participle",
        "VBN": "Verb, past participle",
        "VBP": "Verb, non-3rd person singular present",
        "VBZ": "Verb, 3rd person singular present",
        "WDT": "Wh-determiner",
        "WP": "Wh-pronoun",
        "WP$": "Possessive wh-pronoun",
        "WRB": "Wh-adverb",
    }

    def __init__(self):
        pass

    def _tag_text(self, text: str) -> dict[str, int]:
        """
        Internal tagging logic using TextBlob.
        """
        import nltk
        try:
            tokens = nltk.word_tokenize(text)
            tagged = nltk.pos_tag(tokens)
        except Exception as e:
            logger.error(f"NLTK tagging failed: {e}")
            # Fallback to simple split if NLTK fails
            return {}
        
        tag_counts: dict[str, int] = {}
        for _, tag in tagged:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
        return tag_counts

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Returns a dictionary of raw POS tag counts.
        """
        return self._tag_text(text)

    def get_ratios(self, text: str) -> dict[str, float]:
        """
        Calculates normalized ratios for verbs, nouns, and adjectives.
        """
        tags = self._tag_text(text)
        total = sum(tags.values())
        if total == 0:
            return {"verb_ratio": 0.0, "noun_ratio": 0.0, "adjective_ratio": 0.0}
            
        return {
            "verb_ratio": round(sum(v for k, v in tags.items() if k.startswith('VB')) / total, 3),
            "noun_ratio": round(sum(v for k, v in tags.items() if k.startswith('NN')) / total, 3),
            "adjective_ratio": round(sum(v for k, v in tags.items() if k.startswith('JJ')) / total, 3),
        }

    def get_summary(self, text: str) -> dict[str, float]:
        """Alias for get_ratios for legacy support"""
        return self.get_ratios(text)

    def get_tag_description(self, tag: str) -> str:
        """
        Returns the human-readable description of a POS tag.
        """
        return self.TAG_DESCRIPTIONS.get(tag, "Unknown tag")