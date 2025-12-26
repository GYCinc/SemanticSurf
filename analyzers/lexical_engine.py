import csv
import os
import json
import re
from typing import List, Dict, Set, Optional, Any
import nltk

class LexicalEngine:
    """
    High-fidelity deterministic vocabulary matcher.
    Implements the "Suffix-Stripper" heuristic lemmatizer to avoid heavy NLP dependencies.
    Includes "Cognitive Effort" via fuzzy matching to credit mispronunciations.
    """
    def __init__(self, ngsl_path: Optional[str] = None, coca_path: Optional[str] = None, confidence_threshold: float = 0.85, fuzzy_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        self.fuzzy_threshold = fuzzy_threshold
        self.ngsl_vocab: Set[str] = set()
        self.coca_vocab: Set[str] = set()
        self.combined_vocab_list: List[str] = []
        
        # Default paths if not provided (based on gitenglishhub structure)
        base_lexical = "/Users/safeSpacesBro/gitenglishhub/LEXICAL RESOURCES"
        ngsl_path = ngsl_path or os.path.join(base_lexical, "NGSL_1.2_lemmatized_for_teaching.csv")
        coca_path = coca_path or os.path.join(base_lexical, "COCA-60000-Vocabulary-List.txt")

        if os.path.exists(ngsl_path):
            self.ngsl_vocab = self._load_ngsl(ngsl_path)
            
        if os.path.exists(coca_path):
            self.coca_vocab = self._load_coca(coca_path)
            
        self.combined_vocab_list = list(self.ngsl_vocab.union(self.coca_vocab))

    def _load_ngsl(self, path: str) -> Set[str]:
        vocab = set()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row or row[0].startswith('#'):
                        continue
                    for item in row:
                        word = item.strip().lower()
                        if word: vocab.add(word)
        except Exception: pass
        return vocab

    def _load_coca(self, path: str) -> Set[str]:
        vocab = set()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('RANK') or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 3:
                        word = parts[2].strip().lower()
                        if word.isalpha(): vocab.add(word)
        except Exception: pass
        return vocab

    def find_fuzzy_match(self, word: str) -> Optional[str]:
        """
        Uses difflib to find a close match in the whitelist for 'cognitive effort' credit.
        """
        import difflib
        # Only fuzzy match if the word is long enough to avoid being too broad
        if len(word) < 4: return None
        matches = difflib.get_close_matches(word, self.combined_vocab_list, n=1, cutoff=self.fuzzy_threshold)
        return matches[0] if matches else None

    def lemmatize(self, word: str) -> str:
        """
        Returns the heuristic stem of a word if it's found in the whitelist.
        """
        w = word.lower()
        if w in self.ngsl_vocab or w in self.coca_vocab:
            return w
            
        suffixes = ['s', 'ed', 'ing', 'es', 'd']
        for suffix in suffixes:
            if w.endswith(suffix):
                stem = w[:-len(suffix)]
                if stem in self.coca_vocab or stem in self.ngsl_vocab:
                    return stem
                
                if len(stem) > 2 and stem[-1] == stem[-2]:
                    if stem[:-1] in self.coca_vocab or stem[:-1] in self.ngsl_vocab:
                        return stem[:-1]
                        
                if suffix == 'es' and w.endswith('ies'):
                    stem_y = w[:-3] + 'y'
                    if stem_y in self.coca_vocab or stem_y in self.ngsl_vocab:
                         return stem_y
        return w

    def resolve_token(self, word: str) -> Optional[str]:
        """
        Resolves a word to its canonical dictionary form.
        Priority:
        1. Exact Match (e.g. "talking" in list) -> Returns "talking"
        2. Lemma Match (e.g. "talks" -> "talk" in list) -> Returns "talk" (Stemming behavior)
        3. Fuzzy Match (e.g. "talkin" -> "talking") -> Returns "talking"
        """
        w = word.lower()
        # 1. Exact Match
        if w in self.ngsl_vocab or w in self.coca_vocab:
            return w
        
        # 2. Check if lemma is in list (Implicitly valid)
        # Note: If user wants "talks" distinct from "talk", we only get "talks" if "talks" is in the dict.
        # Most frequency lists contain inflected forms. IF NOT, this fallback collapses to lemma.
        # This is acceptable standard behavior for unlisted inflections.
        lemma = self.lemmatize(w)
        if lemma in self.ngsl_vocab or lemma in self.coca_vocab:
            return lemma
            
        # 3. Fuzzy Match (Cognitive Effort)
        fuzzy = self.find_fuzzy_match(w)
        if fuzzy:
            return fuzzy
            
        return None

    def is_in_whitelist(self, word: str) -> bool:
        return self.resolve_token(word) is not None
        
    def is_academic(self, word: str) -> bool:
        return word.lower() in self.ngsl_vocab

    def filter_low_confidence(self, transcript_words: List[Dict]) -> List[Dict]:
        return [w for w in transcript_words if float(w.get('confidence', 0.0)) >= self.confidence_threshold]

    def analyze_production(self, words: List[Dict]) -> Dict:
        """
        Reconstructs the transcript while tagging words with high-fidelity attributes.
        """
        validated = self.filter_low_confidence(words)
        
        # Extract text tokens for POS tagging
        tokens = [w.get('text', '').strip(".,?!\"'") for w in validated]
        
        # Download NLTK data if needed (idempotent-ish check)
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger_eng')
        except LookupError:
            nltk.download('averaged_perceptron_tagger_eng', quiet=True)
            
        # Run POS tagging
        try:
            pos_tags = nltk.pos_tag(tokens)
        except Exception: # Fallback if download failed
             pos_tags = [(t, 'NN') for t in tokens]

        reconstructed = []
        unknown_count = 0
        
        for i, w_obj in enumerate(validated):
            text_raw = w_obj.get('text', '')
            text_clean = text_raw.strip(".,?!\"'").lower()
            if not text_clean: continue
            
            # Resolve to canonical form
            resolved = self.resolve_token(text_clean)
            is_whitelisted = resolved is not None
            
            if not is_whitelisted:
                unknown_count += 1
            
            # Get POS tag from the parallel list
            pos_tag = pos_tags[i][1] if i < len(pos_tags) else 'NN'

            reconstructed.append({
                "text": text_raw,
                "start": w_obj.get('start'),
                "end": w_obj.get('end'),
                "confidence": w_obj.get('confidence'),
                "is_academic": self.is_academic(resolved) if resolved else False,
                "is_whitelisted": is_whitelisted,
                "lemma": self.lemmatize(text_clean),
                "resolved_word": resolved,  # Key addition for exact form tracking
                "pos": pos_tag
            })
            
        return {
            "words": reconstructed,
            "raw_text": " ".join([w['text'] for w in reconstructed]),
            "unknown_ratio": unknown_count / len(reconstructed) if reconstructed else 0,
            "unknown_count": unknown_count
        }

    def analyze_transcript_string(self, text: str) -> Dict:
        from AssemblyAIv2.analyzers.sentence_chunker import chunk_transcript
        temp_path = "/tmp/temp_transcript.txt"
        with open(temp_path, "w") as f:
            f.write(text)
        words = [{"text": w, "confidence": 1.0} for w in re.findall(r'\b\w+\b', text)]
        return self.analyze_production(words)
