
import os
import csv
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class VerbAnalyzer:
    def __init__(self, data_path: str = "data/verb_patterns/verb_transitivity.tsv"):
        self.verbs: Dict[str, Dict[str, float]] = {}
        self._load_data(data_path)

    def _load_data(self, path: str):
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

    def get_stats(self, verb: str) -> Optional[Dict[str, float]]:
        return self.verbs.get(verb.lower())

    def check_usage_probability(self, verb: str, usage_type: str) -> float:
        """
        usage_type: 'intransitive', 'transitive', 'ditransitive'
        Returns probability (0-1) or 0 if verb unknown.
        """
        stats = self.get_stats(verb)
        if not stats:
            return 0.0
        return stats.get(usage_type, 0.0)

    def analyze(self, text: str) -> dict:
        """
        Scans for verbs and potential transitivity issues.
        Only looks up words identified as verbs by POS tagging.
        """
        from textblob import TextBlob
        blob = TextBlob(text)
        
        irregular_errors = []
        
        for word, tag in blob.tags:
            # Only process if TextBlob thinks it is a verb (VB, VBD, VBG, VBN, VBP, VBZ)
            if tag.startswith('VB'):
                word_lower = word.lower()
                stats = self.get_stats(word_lower)
                if stats:
                    irregular_errors.append({
                        "verb": word,
                        "tag": tag,
                        "stats": stats
                    })
                
        return {
            "irregular_errors": irregular_errors,
            "total_verbs_found": len(irregular_errors)
        }
