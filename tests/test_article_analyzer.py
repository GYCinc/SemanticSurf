import unittest
from analyzers.article_analyzer import ArticleAnalyzer

class TestArticleAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ArticleAnalyzer()

    def test_correct_usage(self):
        # Should return no errors
        self.assertEqual(self.analyzer.analyze("I have a cat."), [])
        self.assertEqual(self.analyzer.analyze("I saw an elephant."), [])
        self.assertEqual(self.analyzer.analyze("It is an honor."), [])
        self.assertEqual(self.analyzer.analyze("Go to a university."), [])

    def test_incorrect_a_for_an(self):
        errors = self.analyzer.analyze("I saw a elephant.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['correction'], "an elephant")

    def test_incorrect_an_for_a(self):
        errors = self.analyzer.analyze("It is an car.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['correction'], "a car")

    def test_exceptions_honor(self):
        # 'honor' starts with H but vowel sounds -> 'an honor' is correct.
        # 'a honor' is incorrect.
        errors = self.analyzer.analyze("It is a honor.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['correction'], "an honor")

    def test_exceptions_university(self):
        # 'university' starts with U but consonant sound (y) -> 'a university' is correct.
        # 'an university' is incorrect.
        errors = self.analyzer.analyze("He goes to an university.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['correction'], "a university")

    def test_case_insensitivity(self):
        errors = self.analyzer.analyze("A Apple is red.")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['correction'], "an apple")

if __name__ == "__main__":
    unittest.main()
