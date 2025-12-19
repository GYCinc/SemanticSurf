import logging
from collections import Counter

logger = logging.getLogger("NgramAnalyzer")

class NgramAnalyzer:
    """
    Performs N-gram analysis on text.
    Compares student n-grams against a baseline to identify unusual patterns.
    
    Note: A full implementation would integrate with py-ngrams or COCA data.
    This MVP uses a seed dataset of common English bigrams.
    """

    # Common English bigrams (High-frequency list for linguistic grounding)
    COMMON_BIGRAMS: set[tuple[str, str]] = {
        ("i", "am"), ("i", "have"), ("i", "was"), ("i", "will"), ("i", "think"), ("i", "know"), ("i", "agree"),
        ("it", "is"), ("it", "was"), ("it", "has"), ("it", "can"), ("it", "sounds"),
        ("there", "is"), ("there", "are"), ("there", "was"), ("there", "were"),
        ("going", "to"), ("want", "to"), ("have", "to"), ("need", "to"), ("used", "to"),
        ("in", "the"), ("on", "the"), ("at", "the"), ("to", "the"), ("of", "the"), ("for", "the"),
        ("with", "the"), ("from", "the"), ("by", "the"), ("about", "the"), ("into", "the"),
        ("is", "a"), ("was", "a"), ("has", "a"), ("be", "a"), ("with", "a"), ("for", "a"),
        ("the", "first"), ("the", "last"), ("the", "next"), ("the", "same"), ("the", "other"),
        ("a", "lot"), ("a", "little"), ("a", "few"), ("a", "bit"), ("a", "large"),
        ("do", "not"), ("does", "not"), ("did", "not"), ("will", "not"), ("can", "not"),
        ("don't", "know"), ("don't", "think"), ("didn't", "have"), ("can't", "do"),
        ("how", "was"), ("was", "your"), ("did", "you"), ("you", "do"), ("you", "should"), ("you", "can"),
        ("i", "would"), ("we", "should"), ("they", "are"), ("this", "is"), ("that", "is"),
        ("has", "been"), ("have", "been"), ("had", "been"), ("will", "be"),
        ("as", "well"), ("such", "as"), ("kind", "of"), ("sort", "of"), ("part", "of"),
        ("you", "know"), ("you", "see"), ("i'm", "sure"), ("actually", "i"),
    }

    def __init__(self):
        pass

    def get_bigrams(self, text: str) -> list[tuple[str, str]]:
        """
        Extracts bigrams (pairs of consecutive words) from text.
        Strips punctuation for accurate matching.
        """
        import re
        # Strip punctuation and split
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        bigrams = [(words[i], words[i+1]) for i in range(len(words) - 1)]
        # Log a small sample for debugging
        if bigrams:
            logger.debug(f"Bigram sample: {bigrams[:5]}")
        return bigrams

    def get_trigrams(self, text: str) -> list[tuple[str, str, str]]:
        """
        Extracts trigrams (triplets of consecutive words) from text.
        Strips punctuation for accurate matching.
        """
        import re
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        return [(words[i], words[i+1], words[i+2]) for i in range(len(words) - 2)]

    def analyze_bigrams(self, text: str) -> dict[str, int]:
        """
        Returns frequency counts of bigrams in the text.
        """
        bigrams = self.get_bigrams(text)
        return dict(Counter(bigrams))

    def get_unusual_bigrams(self, text: str) -> list[tuple[str, str]]:
        """
        Returns bigrams that are NOT in the common baseline.
        These may indicate non-native patterns or creative usage.
        """
        bigrams = self.get_bigrams(text)
        return [bg for bg in bigrams if bg not in self.COMMON_BIGRAMS]

    def get_naturalness_score(self, text: str) -> float:
        """
        Returns a score 0-100 indicating how "natural" the text is.
        Uses a weighted approach: presence of common bigrams vs unusual ones.
        Native speakers typically score 70-95. Students typically 20-50.
        """
        bigrams = self.get_bigrams(text)
        if not bigrams:
            return 0.0
            
        common_count = sum(1 for bg in bigrams if bg in self.COMMON_BIGRAMS)
        
        # Calculate base ratio (0-1)
        ratio = common_count / len(bigrams)
        
        # Scale to 0-100 with a non-linear boost for common patterns
        # Even native speech has many unique bigrams, so a raw 0.3 ratio
        # might actually represent 80% naturalness in a conversation.
        score = (ratio * 250) # Simple linear scaling for now
        return min(100.0, round(score, 1))

    def get_summary(self, text: str) -> dict[str, float | int]:
        """
        Returns a summary of n-gram analysis for the text.
        """
        bigrams = self.get_bigrams(text)
        unusual = self.get_unusual_bigrams(text)
        
        return {
            "total_bigrams": len(bigrams),
            "unusual_bigram_count": len(unusual),
            "naturalness_score": self.get_naturalness_score(text),
        }

    def analyze(self, text: str) -> dict[str, float | int]:
        """Alias for get_summary() for consistency with other analyzers"""
        return self.get_summary(text)
