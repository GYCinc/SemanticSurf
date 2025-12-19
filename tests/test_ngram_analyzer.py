import unittest
from analyzers.ngram_analyzer import NgramAnalyzer

class TestNgramAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = NgramAnalyzer()

    def test_get_bigrams(self):
        text = "I am going to the store."
        bigrams = self.analyzer.get_bigrams(text)
        self.assertIn(("i", "am"), bigrams)
        self.assertIn(("going", "to"), bigrams)
        self.assertIn(("to", "the"), bigrams)

    def test_get_trigrams(self):
        text = "I am going to the store."
        trigrams = self.analyzer.get_trigrams(text)
        self.assertIn(("i", "am", "going"), trigrams)
        self.assertIn(("going", "to", "the"), trigrams)

    def test_naturalness_score(self):
        # A sentence with common phrases should have higher naturalness
        natural_text = "I am going to the store."
        score = self.analyzer.get_naturalness_score(natural_text)
        self.assertGreater(score, 0.3)

    def test_unusual_bigrams(self):
        # A sentence with uncommon word pairs
        unusual_text = "Penguin flamingo zebra giraffe."
        unusual = self.analyzer.get_unusual_bigrams(unusual_text)
        # All bigrams should be unusual
        self.assertEqual(len(unusual), 3)

    def test_summary(self):
        text = "I have been to the store."
        summary = self.analyzer.get_summary(text)
        self.assertIn("total_bigrams", summary)
        self.assertIn("unusual_bigram_count", summary)
        self.assertIn("naturalness_score", summary)

if __name__ == "__main__":
    unittest.main()
