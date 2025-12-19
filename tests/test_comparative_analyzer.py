import unittest
from analyzers.comparative_analyzer import ComparativeAnalyzer

class TestComparativeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ComparativeAnalyzer()

    def test_analyze_returns_all_keys(self):
        tutor = "I think you're doing well. Let's try another exercise."
        student = "I think is good. We try more."
        result = self.analyzer.analyze(tutor, student)
        self.assertIn("tutor", result)
        self.assertIn("student", result)
        self.assertIn("comparison", result)

    def test_tutor_metrics(self):
        tutor = "The quick brown fox jumps over the lazy dog."
        student = "Dog is run fast."
        result = self.analyzer.analyze(tutor, student)
        self.assertIn("word_count", result["tutor"])
        self.assertIn("naturalness_score", result["tutor"])
        self.assertIn("lexical_diversity", result["tutor"])

    def test_comparison_gap(self):
        tutor = "I am going to the store to buy some groceries."
        student = "I go store buy food."
        result = self.analyzer.analyze(tutor, student)
        # Tutor should have higher naturalness (more common bigrams)
        self.assertGreaterEqual(result["comparison"]["naturalness_gap"], 0)

    def test_context_string(self):
        tutor = "This is a test sentence."
        student = "This test sentence."
        context = self.analyzer.get_context_string(tutor, student)
        self.assertIn("Comparative Analysis", context)
        self.assertIn("Tutor", context)
        self.assertIn("Student", context)

if __name__ == "__main__":
    unittest.main()
