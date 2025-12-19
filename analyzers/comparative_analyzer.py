import logging
from typing import Optional

logger = logging.getLogger("ComparativeAnalyzer")

class ComparativeAnalyzer:
    """
    Compares student speech metrics against tutor (native speaker) speech.
    Provides a benchmark for naturalness, fluency, rhythm, and other linguistic features.
    """

    def __init__(self):
        pass

    def analyze(self, tutor_text: str, student_text: str) -> dict[str, dict[str, float]]:
        """
        Performs a comprehensive comparison between tutor and student speech.
        Returns metrics for both, plus a comparison delta.
        """
        from textblob import TextBlob
        from .pos_analyzer import POSAnalyzer
        from .ngram_analyzer import NgramAnalyzer
        
        pos_analyzer = POSAnalyzer()
        ngram_analyzer = NgramAnalyzer()
        
        # === Basic Stats ===
        tutor_words = tutor_text.split()
        student_words = student_text.split()
        
        tutor_word_count = len(tutor_words)
        student_word_count = len(student_words)
        
        tutor_avg_word_len = sum(len(w) for w in tutor_words) / max(tutor_word_count, 1)
        student_avg_word_len = sum(len(w) for w in student_words) / max(student_word_count, 1)
        
        # === POS Ratios ===
        tutor_pos = pos_analyzer.get_summary(tutor_text)
        student_pos = pos_analyzer.get_summary(student_text)
        
        # === N-gram Naturalness ===
        tutor_ngram_data = ngram_analyzer.get_summary(tutor_text)
        student_ngram_data = ngram_analyzer.get_summary(student_text)
        
        # DEBUG LOGS FOR AUDIT
        print(f"DEBUG: Tutor Ngram Data: {tutor_ngram_data}")
        print(f"DEBUG: Student Ngram Data: {student_ngram_data}")
        
        # === Sentence Complexity (avg words per sentence as proxy) ===
        tutor_sentences = tutor_text.count('.') + tutor_text.count('!') + tutor_text.count('?')
        student_sentences = student_text.count('.') + student_text.count('!') + student_text.count('?')
        
        tutor_avg_sentence_len = tutor_word_count / max(tutor_sentences, 1)
        student_avg_sentence_len = student_word_count / max(student_sentences, 1)
        
        # === Lexical Diversity (Type-Token Ratio) ===
        tutor_unique = len(set(w.lower() for w in tutor_words))
        student_unique = len(set(w.lower() for w in student_words))
        
        tutor_ttr = tutor_unique / max(tutor_word_count, 1)
        student_ttr = student_unique / max(student_word_count, 1)
        
        # === NEW: Direct Tutor Overlap (Personalized Naturalness) ===
        tutor_bigrams_list = ngram_analyzer.get_bigrams(tutor_text)
        student_bigrams_list = ngram_analyzer.get_bigrams(student_text)
        
        tutor_bigrams_set = set(tutor_bigrams_list)
        
        # Calculate overlap
        overlap_bigrams = [bg for bg in student_bigrams_list if bg in tutor_bigrams_set]
        overlap_count = len(overlap_bigrams)
        tutor_overlap_ratio = overlap_count / max(len(student_bigrams_list), 1)
        
        # === Build Result ===
        result = {
            "tutor": {
                "word_count": tutor_word_count,
                "avg_word_length": round(tutor_avg_word_len, 2),
                "avg_sentence_length": round(tutor_avg_sentence_len, 2),
                "lexical_diversity": round(tutor_ttr, 3),
                "naturalness_score": tutor_ngram_data['naturalness_score'],
                "verb_ratio": tutor_pos['verb_ratio'],
                "noun_ratio": tutor_pos['noun_ratio'],
                "adjective_ratio": tutor_pos['adjective_ratio'],
            },
            "student": {
                "word_count": student_word_count,
                "avg_word_length": round(student_avg_word_len, 2),
                "avg_sentence_length": round(student_avg_sentence_len, 2),
                "lexical_diversity": round(student_ttr, 3),
                "naturalness_score": student_ngram_data['naturalness_score'],
                "verb_ratio": student_pos['verb_ratio'],
                "noun_ratio": student_pos['noun_ratio'],
                "adjective_ratio": student_pos['adjective_ratio'],
                "tutor_overlap_score": round(tutor_overlap_ratio * 100, 1) # 0-100%
            },
            "comparison": {
                "word_count_ratio": round(student_word_count / max(tutor_word_count, 1), 2),
                "naturalness_gap": round(tutor_ngram_data['naturalness_score'] - student_ngram_data['naturalness_score'], 3),
                "lexical_diversity_gap": round(tutor_ttr - student_ttr, 3),
                "avg_sentence_length_gap": round(tutor_avg_sentence_len - student_avg_sentence_len, 2),
                "tutor_overlap_pct": round(tutor_overlap_ratio * 100, 1)
            }
        }
        
        return result

    def get_context_string(self, tutor_text: str, student_text: str) -> str:
        """
        Returns a formatted string suitable for injection into an LLM prompt.
        """
        analysis = self.analyze(tutor_text, student_text)
        
        tutor = analysis['tutor']
        student = analysis['student']
        comp = analysis['comparison']
        
        return f"""
[Comparative Analysis: Tutor (Native) vs Student]
| Metric              | Tutor  | Student | Gap      |
|---------------------|--------|---------|----------|
| Naturalness Score   | {tutor['naturalness_score']:.3f} | {student['naturalness_score']:.3f} | {comp['naturalness_gap']:+.3f} |
| Lexical Diversity   | {tutor['lexical_diversity']:.3f} | {student['lexical_diversity']:.3f} | {comp['lexical_diversity_gap']:+.3f} |
| Avg Sentence Length | {tutor['avg_sentence_length']:.1f} | {student['avg_sentence_length']:.1f} | {comp['avg_sentence_length_gap']:+.1f} |
| Verb Ratio          | {tutor['verb_ratio']:.3f} | {student['verb_ratio']:.3f} |          |
| Noun Ratio          | {tutor['noun_ratio']:.3f} | {student['noun_ratio']:.3f} |          |
| Word Count          | {tutor['word_count']} | {student['word_count']} |          |
"""

    def compare(self, student_data: dict, tutor_data: dict) -> dict:
        """
        Alias for pipeline compatibility. Extracts text and runs analyze().
        """
        return self.analyze(tutor_data.get('text', ''), student_data.get('text', ''))
