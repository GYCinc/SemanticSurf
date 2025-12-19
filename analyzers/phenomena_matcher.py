import json
import re
import logging
from pathlib import Path

logger = logging.getLogger("PhenomenaPatternMatcher")

class PhenomenaPatternMatcher:
    """
    Matches student speech against the full unified_phenomena.json corpus.
    Uses the triggerPattern regex from each phenomenon for detection.
    """

    def __init__(self, corpus_path: str | None = None):
        """
        Load the phenomena corpus from JSON.
        """
        if corpus_path is None:
            # Default path to the local phenomena corpus
            corpus_path = str(Path(__file__).parent.parent / "data" / "unified_phenomena.json")
        
        self.phenomena: list[dict] = []
        self.patterns: list[tuple[re.Pattern, dict]] = []
        
        try:
            with open(corpus_path, 'r', encoding='utf-8') as f:
                self.phenomena = json.load(f)
            
            # Pre-compile regex patterns for efficiency
            compiled = 0
            for phen in self.phenomena:
                pattern_str = phen.get("triggerPattern", "")
                if pattern_str and pattern_str.strip():
                    try:
                        compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                        self.patterns.append((compiled_pattern, phen))
                        compiled += 1
                    except re.error as e:
                        # Skip invalid regex patterns
                        pass
            
            logger.info(f"✅ Loaded {len(self.phenomena)} phenomena, {compiled} valid patterns compiled")
            
        except FileNotFoundError:
            logger.warning(f"⚠️ Phenomena corpus not found at {corpus_path}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse phenomena JSON: {e}")

    def match(self, text: str) -> list[dict]:
        """
        Match text against all phenomena patterns.
        Returns list of matched phenomena with context.
        """
        matches = []
        text_lower = text.lower()
        
        for pattern, phen in self.patterns:
            if pattern.search(text_lower):
                matches.append({
                    "phenomenon_id": phen.get("phenomenon_id", ""),
                    "item": phen.get("itemName", ""),
                    "category": phen.get("publicCategory", "Unknown"),
                    "subcategory": phen.get("subcategory", ""),
                    "context": f"Matched in: \"{text[:100]}...\"" if len(text) > 100 else f"Matched in: \"{text}\"",
                    "explanation": phen.get("l1Interference", phen.get("explanation", "")),
                    "correction": phen.get("exampleCorrections", ""),
                    "example_error": phen.get("exampleErrors", ""),
                    "cefr_level": phen.get("cefrLevel", ""),
                    "severity": phen.get("severity", ""),
                    "confidence": float(phen.get("confidenceScore", 0.7)),
                    "source": phen.get("source", "unified_phenomena"),
                })
        
        return matches

    def get_stats(self) -> dict[str, int]:
        """Returns statistics about the loaded corpus."""
        return {
            "total_phenomena": len(self.phenomena),
            "valid_patterns": len(self.patterns),
        }
