import re
import json
import logging
from pathlib import Path
from typing import Any, final

logger = logging.getLogger("ArticleAnalyzer")

@final
class ArticleAnalyzer:
    """
    Advanced Article Analyzer (PATSI-Lite).
    Combines:
    1. Standard 'a/an' phonetic mismatches.
    2. Rule-based detection using 'unified_phenomena.json' (The "PATSI" rules).
    """

    vowels: set[str]
    an_exceptions: list[str]
    a_exceptions: list[str]
    json_rules: list[dict[str, Any]]

    def __init__(self):
        # --- Standard Logic Setup ---
        self.vowels = set("aeiou")
        self.an_exceptions = ["hour", "honest", "heir", "honor"] 
        self.a_exceptions = ["university", "united", "unique", "useful", "usage", "eu", "one", "utopia", "union", "unit", "user", "unicorn", "uniform"]
        
        # --- Unified Phenomena Setup ---
        self.json_rules = []
        self._load_unified_rules()

    def _load_unified_rules(self):
        """Loads article-specific rules from the unified_phenomena.json definition."""
        try:
            # Path relative to this file: ../data/unified_phenomena.json
            base_path = Path(__file__).resolve().parent.parent / "data" / "unified_phenomena.json"
            if base_path.exists():
                with open(base_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                count = 0
                for item in data:
                    # Filter for Article/Grammar rules relevant to articles
                    subcat = item.get("subcategory", "")
                    cat = item.get("publicCategory", "")
                    name = item.get("itemName", "").lower()
                    
                    is_article_rule = (
                        "Article" in subcat or 
                        "Article" in cat or 
                        "article" in name
                    )
                    
                    if is_article_rule and item.get("triggerPattern"):
                        try:
                            self.json_rules.append({
                                "regex": re.compile(item["triggerPattern"], re.IGNORECASE),
                                "meta": item
                            })
                            count += 1
                        except re.error:
                            logger.warning(f"Invalid regex for {item.get('phenomenon_id')}")
                            
                logger.info(f"📚 ArticleAnalyzer loaded {count} advanced rules from Unified Phenomena.")
            else:
                logger.warning("⚠️ unified_phenomena.json not found. Advanced article rules disabled.")
                
        except Exception as e:
            logger.error(f"Failed to load unified rules: {e}")

    def analyze(self, text: str) -> list[dict[str, str]]:
        errors = []
        
        # 1. Standard 'a/an' Check
        matches = re.finditer(r'\b(a|an)\s+([a-z]+)\b', text, re.IGNORECASE)
        for match in matches:
            article = match.group(1).lower()
            next_word = match.group(2).lower()
            needs_an = self._starts_with_vowel_sound(next_word)
            
            if article == "a" and needs_an:
                errors.append({
                    "item": f"{article} {next_word}",
                    "match": f"{article} {next_word}",
                    "correction": f"an {next_word}",
                    "explanation": f"Use 'an' before '{next_word}' because it starts with a vowel sound.",
                    "source": "PhoneticRule"
                })
            elif article == "an" and not needs_an:
                errors.append({
                    "item": f"{article} {next_word}",
                    "match": f"{article} {next_word}",
                    "correction": f"a {next_word}",
                    "explanation": f"Use 'a' before '{next_word}' because it starts with a consonant sound.",
                    "source": "PhoneticRule"
                })

        # 2. Unified Phenomena Check (PATSI)
        for rule in self.json_rules:
            pattern = rule["regex"]
            p_meta = rule["meta"]
            
            p_matches = pattern.finditer(text)
            for pm in p_matches:
                # Avoid dupes if same text caught by basic rule
                matched_text = pm.group(0)
                if not any(e['match'] == matched_text for e in errors):
                     errors.append({
                        "item": p_meta.get("itemName"),
                        "match": matched_text,
                        "correction": p_meta.get("exampleCorrections", "").split('|')[0], # Take first correction hint
                        "explanation": p_meta.get("l1Interference") or p_meta.get("explanation") or "Article usage error.",
                        "source": "UnifiedPhenomena"
                    })

        return errors

    @final
    def _starts_with_vowel_sound(self, word: str) -> bool:
        """Determines if a word starts with a vowel sound."""
        if not word: return False
        
        # Check explicit consonant-sound exceptions (u-words)
        if word in self.a_exceptions:
            return False
            
        # Check explicit vowel-sound exceptions (silent h)
        if word in self.an_exceptions:
            return True
            
        # Default rule
        return word[0] in self.vowels
