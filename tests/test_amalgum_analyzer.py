import unittest
from analyzers.amalgum_analyzer import AmalgumAnalyzer

class TestAmalgumAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = AmalgumAnalyzer()

    def test_academic_classification(self):
        text = "Moreover, the hypothesis therefore demonstrates a significant correlation."
        genre = self.analyzer.get_genre_classification(text)
        self.assertEqual(genre, "Academic")
        scores = self.analyzer.analyze_register(text)
        self.assertTrue(scores['academic'] > 0)
        self.assertEqual(scores['conversational'], 0)

    def test_conversational_classification(self):
        text = "It's like, kind of basically just stuff you know?"
        genre = self.analyzer.get_genre_classification(text)
        self.assertEqual(genre, "Conversational")
        scores = self.analyzer.analyze_register(text)
        self.assertTrue(scores['conversational'] > 0)
        self.assertEqual(scores['academic'], 0)

    def test_neutral_classification(self):
        text = "The cat sat on the mat."
        genre = self.analyzer.get_genre_classification(text)
        self.assertEqual(genre, "Neutral")

if __name__ == "__main__":
    unittest.main()
