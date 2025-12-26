import os
import csv
import json
import re
import logging
from pathlib import Path
from typing import TypedDict, cast, Any

logger = logging.getLogger(__name__)

class VerbStats(TypedDict):
    intransitive: float
    transitive: float
    ditransitive: float

class IrregularErrorDetails(TypedDict):
    verb: str
    tag: str
    stats: VerbStats

class AnalysisOutput(TypedDict):
    irregular_errors: list[IrregularErrorDetails]
    pattern_matches: list[dict[str, Any]]
    total_verbs_found: int

class VerbAnalyzer:
    """
    Advanced Verb Analyzer.
    Combines:
    1. Statistical Transitivity Analysis (via verb_transitivity.tsv)
    2. Rule-based detection using 'unified_phenomena.json' (PATSI Rules)
    """

    def __init__(self, data_path: str | None = None):
        self.verbs: dict[str, VerbStats] = {}
        self.json_rules: list[dict[str, Any]] = []
        
        # 1. Load Transitivity Data
        if data_path is None:
            # Resolve relative to the AssemblyAIv2 package root
            # This file is at AssemblyAIv2/analyzers/verb_analyzer.py
            # We want AssemblyAIv2/data/verb_patterns/verb_transitivity.tsv
            base = Path(__file__).resolve().parent.parent 
            data_path = str(base / "data/verb_patterns/verb_transitivity.tsv")
        
        self._load_transitivity_data(data_path)
        
        # 2. Load Unified Phenomena Rules
        self._load_unified_rules()

    def _load_transitivity_data(self, path: str):
        if not os.path.exists(path):
            logger.error(f"Verb transitivity data not found at {path}")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    verb = row['verb']
                    try:
                        self.verbs[verb] = {
                            "intransitive": float(row['percent_intrans']),
                            "transitive": float(row['percent_trans']),
                            "ditransitive": float(row['percent_ditrans'])
                        }
                    except ValueError:
                        continue
            logger.info(f"Loaded transitivity data for {len(self.verbs)} verbs")
        except Exception as e:
            logger.error(f"Failed to load verb data: {e}")

    def _load_unified_rules(self):
        """Loads verb-related rules from unified_phenomena.json."""
        try:
            base_path = Path(__file__).resolve().parent.parent / "data" / "unified_phenomena.json"
            if base_path.exists():
                with open(base_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                count = 0
                for item in data:
                    # Filter for Verb-related rules
                    subcat = item.get("subcategory", "")
                    cat = item.get("publicCategory", "")
                    name = item.get("itemName", "").lower()
                    
                    is_verb_rule = (
                        "Verb" in subcat or 
                        "Verb" in cat or
                        "Grammar" in subcat # Many verb errors are just labeled Grammar
                    )
                    
                    # Only add if it looks like a regex pattern we can use
                    if is_verb_rule and item.get("triggerPattern") and len(item["triggerPattern"]) > 3:
                        try:
                            self.json_rules.append({
                                "regex": re.compile(item["triggerPattern"], re.IGNORECASE),
                                "meta": item
                            })
                            count += 1
                        except re.error:
                            continue
                            
                logger.info(f"📚 VerbAnalyzer loaded {count} advanced rules from Unified Phenomena.")
            else:
                logger.warning("⚠️ unified_phenomena.json not found. Advanced verb rules disabled.")
                
        except Exception as e:
            logger.error(f"Failed to load unified verb rules: {e}")

    def get_stats(self, verb: str) -> VerbStats | None:
        return self.verbs.get(verb.lower())

    def analyze(self, text: str) -> AnalysisOutput:
        """
        Scans for verbs and potential transitivity issues + Regex Patterns.
        """
        # --- Part 1: Transitivity/POS Scan ---
        irregular_errors: list[IrregularErrorDetails] = []
        try:
            import nltk # type: ignore
            try:
                tokens = cast(list[str], nltk.word_tokenize(text)) # type: ignore
                tagged = cast(list[tuple[str, str]], nltk.pos_tag(tokens)) # type: ignore
            except LookupError:
                nltk.download('punkt') # type: ignore
                nltk.download('averaged_perceptron_tagger') # type: ignore
                tokens = cast(list[str], nltk.word_tokenize(text)) # type: ignore
                tagged = cast(list[tuple[str, str]], nltk.pos_tag(tokens)) # type: ignore
                
            for word, tag in tagged:
                if tag.startswith('VB'):
                    word_lower = word.lower()
                    stats = self.get_stats(word_lower)
                    if stats:
                        irregular_errors.append({
                            "verb": word,
                            "tag": tag,
                            "stats": stats
                        })
        except Exception as e:
            logger.warning(f"NLTK tagging failed in VerbAnalyzer: {e}")

        # --- Part 2: Unified Phenomena Regex Scan ---
        pattern_matches = []
        for rule in self.json_rules:
            pattern = rule["regex"]
            p_meta = rule["meta"]
            
            p_matches = pattern.finditer(text)
            for pm in p_matches:
                 pattern_matches.append({
                    "item": p_meta.get("itemName"),
                    "match": pm.group(0),
                    "correction": p_meta.get("exampleCorrections", "").split('|')[0],
                    "explanation": p_meta.get("explanation") or p_meta.get("l1Interference") or "Verb usage error.",
                    "source": "UnifiedPhenomena"
                })

        return {
            "irregular_errors": irregular_errors,
            "pattern_matches": pattern_matches,
            "total_verbs_found": len(irregular_errors)
        }
