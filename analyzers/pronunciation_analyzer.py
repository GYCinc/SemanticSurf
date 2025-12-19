import logging
import re

logger = logging.getLogger("PronunciationAnalyzer")

class PronunciationAnalyzer:
    """
    Analyzes transcribed text for potential pronunciation-related errors.
    Based on FAE-CV (Foreign Accented English) patterns.
    
    Note: Since we work with transcriptions (not audio), we detect
    pronunciation issues that manifest as transcription spelling variations
    or phonetically-influenced word substitutions.
    """

    # Common phonetic substitution patterns in transcribed speech
    # These are words that ESL speakers often substitute due to pronunciation difficulties
    PHONETIC_PATTERNS: list[tuple[str, str, str]] = [
        # (pattern, likely_intended, explanation)
        
        # Vowel Confusion (common in many L1 backgrounds)
        (r'\bship\b', "ship/sheep", "Check: intended 'ship' or 'sheep'? (i/iː confusion)"),
        (r'\bsheet\b', "sheet/shit", "Check context for appropriate word"),
        (r'\blive\b', "live/leave", "Check: intended 'live' or 'leave'? (i/iː confusion)"),
        (r'\bfeel\b', "feel/fill", "Check: intended 'feel' or 'fill'?"),
        
        # TH Sound Difficulties
        (r'\btink\b', "think", "TH→T substitution: 'think'"),
        (r'\bting\b', "thing", "TH→T substitution: 'thing'"),
        (r'\bwit\b', "with", "TH→T substitution: 'with'"),
        (r'\bdis\b', "this", "TH→D substitution: 'this'"),
        (r'\bdat\b', "that", "TH→D substitution: 'that'"),
        (r'\bdem\b', "them", "TH→D substitution: 'them'"),
        (r'\bder\b', "there/their", "TH→D substitution"),
        
        # Final Consonant Deletion
        (r'\bwor\b', "work", "Final consonant deletion: 'work'"),
        (r'\bmos\b', "most", "Final consonant deletion: 'most'"),
        (r'\bjus\b', "just", "Final consonant deletion: 'just'"),
        (r'\blas\b', "last", "Final consonant deletion: 'last'"),
        
        # R/L Confusion (common in East Asian L1)
        (r'\bvely\b', "very", "R→L substitution: 'very'"),
        (r'\blight\b', "right/light", "Check: intended 'right' or 'light'? (r/l confusion)"),
        (r'\brice\b', "rice/lice", "Check context (r/l confusion)"),
        
        # V/W Confusion (common in some L1 backgrounds)
        (r'\bwery\b', "very", "V→W substitution: 'very'"),
        (r'\bwen\b', "when/ven", "Check context"),
        
        # B/V Confusion (common in Spanish L1)
        (r'\bberry\b', "berry/very", "B/V confusion - check context"),
    ]

    def __init__(self):
        pass

    def analyze(self, text: str) -> list[dict[str, str]]:
        """
        Analyzes transcribed text for potential pronunciation-influenced patterns.
        """
        findings = []
        text_lower = text.lower()
        words = text_lower.split()
        
        for pattern, intended, explanation in self.PHONETIC_PATTERNS:
            # Clean pattern for matching
            clean_pattern = pattern.replace(r'\b', '').strip()
            if clean_pattern in words:
                findings.append({
                    "item": clean_pattern,
                    "pattern": intended,
                    "explanation": explanation,
                    "category": "Pronunciation",
                    "confidence": 0.6  # Lower confidence since we're inferring from text
                })
        
        return findings

    def get_phonetic_profile(self, text: str) -> dict[str, list[str]]:
        """
        Returns a profile of potential L1-influenced pronunciations.
        """
        findings = self.analyze(text)
        
        # Categorize by likely L1 influence
        profile: dict[str, list[str]] = {
            "th_substitution": [],
            "vowel_confusion": [],
            "consonant_cluster": [],
            "r_l_confusion": [],
            "other": []
        }
        
        for f in findings:
            exp = f["explanation"].lower()
            if "th" in exp:
                profile["th_substitution"].append(f["item"])
            elif "vowel" in exp or "iː" in exp or "i/" in exp:
                profile["vowel_confusion"].append(f["item"])
            elif "r/l" in exp or "r→l" in exp:
                profile["r_l_confusion"].append(f["item"])
            elif "consonant" in exp:
                profile["consonant_cluster"].append(f["item"])
            else:
                profile["other"].append(f["item"])
        
        return profile
