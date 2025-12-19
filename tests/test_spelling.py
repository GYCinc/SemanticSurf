
import unittest
import sys
import os

# Add parent dir to path so we can import analyzers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.spelling_analyzer import SpellingAnalyzer

class TestSpellingAnalyzer(unittest.TestCase):
    def setUp(self):
        print("Initializing SpellingAnalyzer...")
        self.analyzer = SpellingAnalyzer()

    def test_corpus_loaded(self):
        self.assertTrue(len(self.analyzer.english_words) > 0, "English words corpus should be loaded")
        print(f"Corpus size: {len(self.analyzer.english_words)}")

    def test_detect_misspelling(self):
        word = "recieve"
        is_misspelled = self.analyzer.is_misspelled(word)
        self.assertTrue(is_misspelled, f"'{word}' should be flagged as misspelled")
        print(f"Detected misspelling: {word}")

    def test_detect_correct_word(self):
        word = "receive"
        is_misspelled = self.analyzer.is_misspelled(word)
        self.assertFalse(is_misspelled, f"'{word}' should NOT be flagged as misspelled")

    def test_suggest_correction(self):
        word = "recieve"
        suggestion = self.analyzer.suggest_correction(word)
        self.assertEqual(suggestion, "receive", f"Suggestion for '{word}' should be 'receive'")
        print(f"Suggestion for {word}: {suggestion}")

    def test_check_text(self):
        text = "I will recieve the package tomorrow."
        errors = self.analyzer.check_text(text)
        
        # 'recieve' should be in errors
        found = False
        for err in errors:
            if err['word'] == "recieve":
                found = True
                break
        
        self.assertTrue(found, "Should detect 'recieve' in sentence")
        print(f"Errors found in text: {errors}")

if __name__ == '__main__':
    unittest.main()
