
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.verb_analyzer import VerbAnalyzer

class TestVerbAnalyzer(unittest.TestCase):
    def setUp(self):
        print("Initializing VerbAnalyzer...")
        # Check if file exists relative to CWD or use absolute
        # Assuming running from root
        self.analyzer = VerbAnalyzer()

    def test_data_loaded(self):
        self.assertTrue(len(self.analyzer.verbs) > 0, "Verb data should be loaded")
        print(f"Verbs loaded: {len(self.analyzer.verbs)}")

    def test_expect_stats(self):
        # 'expect' had ~0.79 intransitive in the head output
        stats = self.analyzer.get_stats("expect")
        self.assertIsNotNone(stats)
        print(f"Stats for 'expect': {stats}")
        self.assertGreater(stats['intransitive'], 0.7, "Expect should be > 70% intransitive in this corpus")

    def test_give_stats(self):
        stats = self.analyzer.get_stats("give")
        self.assertIsNotNone(stats)
        print(f"Stats for 'give': {stats}")
        # 'give' is often ditransitive
        self.assertGreater(stats['ditransitive'], 0.1, "Give should have significant ditransitive usage")

    def test_unknown_verb(self):
        stats = self.analyzer.get_stats("xyzyzyz")
        self.assertIsNone(stats)

if __name__ == '__main__':
    unittest.main()
