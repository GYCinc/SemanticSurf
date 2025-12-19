import unittest
from analyzers.pos_analyzer import POSAnalyzer

class TestPOSAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = POSAnalyzer()

    def test_tag_counts(self):
        text = "The quick brown fox jumps over the lazy dog."
        tags = self.analyzer.analyze(text)
        # Should have nouns, adjectives, verbs, etc.
        self.assertIn("NN", tags)  # Noun
        self.assertIn("JJ", tags)  # Adjective
        self.assertIn("VBZ", tags) # Verb 3rd person singular

    def test_verb_ratio(self):
        text = "I run and jump and swim."
        ratio = self.analyzer.get_verb_ratio(text)
        self.assertGreater(ratio, 0.1)  # Should have some verbs

    def test_noun_ratio(self):
        text = "The cat sat on the mat."
        ratio = self.analyzer.get_noun_ratio(text)
        self.assertGreater(ratio, 0.2)  # Should have some nouns

    def test_summary(self):
        text = "The beautiful sunset painted the sky orange."
        summary = self.analyzer.get_summary(text)
        self.assertIn("verb_ratio", summary)
        self.assertIn("noun_ratio", summary)
        self.assertIn("adjective_ratio", summary)

    def test_tag_description(self):
        self.assertEqual(self.analyzer.get_tag_description("VB"), "Verb, base form")
        self.assertEqual(self.analyzer.get_tag_description("NN"), "Noun, singular or mass")
        self.assertEqual(self.analyzer.get_tag_description("UNKNOWN"), "Unknown tag")

if __name__ == "__main__":
    unittest.main()
