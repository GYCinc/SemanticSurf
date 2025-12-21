
import os
import csv
import logging
from pathlib import Path
from typing import TypedDict, cast

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
    total_verbs_found: int

class VerbAnalyzer:
    def __init__(self, data_path: str | None = None):
        self.verbs: dict[str, VerbStats] = {}
        if data_path is None:
            # Resolve relative to the AssemblyAIv2 package root so this works from any CWD.
            data_path = str(Path(__file__).resolve().parents[1] / "data/verb_patterns/verb_transitivity.tsv")
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

    def get_stats(self, verb: str) -> VerbStats | None:
        return self.verbs.get(verb.lower())

    def check_usage_probability(self, verb: str, usage_type: str) -> float:
        """
        usage_type: 'intransitive', 'transitive', 'ditransitive'
        Returns probability (0-1) or 0 if verb unknown.
        """
        stats = self.get_stats(verb)
        if not stats:
            return 0.0
        # We know stats is VerbStats, but usage_type is a string key.
        # TypedDict doesn't support dynamic access safely with .get() in strict mode usually,
        # but runtime dict access works.
        return stats.get(usage_type, 0.0) # type: ignore

    def analyze(self, text: str) -> AnalysisOutput:
        """
        Scans for verbs and potential transitivity issues.
        Only looks up words identified as verbs by POS tagging.
        """
        tokens: list[str] = []
        tagged: list[tuple[str, str]] = []

        try:
            import nltk # type: ignore
            try:
                tokens = cast(list[str], nltk.word_tokenize(text)) # type: ignore
                tagged = cast(list[tuple[str, str]], nltk.pos_tag(tokens)) # type: ignore
            except LookupError:
                # Handle missing NLTK resources
                nltk.download('punkt') # type: ignore
                nltk.download('averaged_perceptron_tagger') # type: ignore
                tokens = cast(list[str], nltk.word_tokenize(text)) # type: ignore
                tagged = cast(list[tuple[str, str]], nltk.pos_tag(tokens)) # type: ignore
                
        except (ImportError, Exception) as e:
            logger.error(f"NLTK tagging failed in VerbAnalyzer: {e}")
            return {
                "irregular_errors": [],
                "total_verbs_found": 0
            }
        
        irregular_errors: list[IrregularErrorDetails] = []
        
        for word, tag in tagged:
            # Only process if NLTK thinks it is a verb (VB, VBD, VBG, VBN, VBP, VBZ)
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
