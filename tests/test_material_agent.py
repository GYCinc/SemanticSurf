import unittest
import asyncio
from schemas import LanguageFeedback, AnalysisCategory
from analyzers.material_agent import MaterialAgent

class TestMaterialAgent(unittest.TestCase):
    def setUp(self):
        # Initialize with mock key
        self.agent = MaterialAgent(api_key="mock")

    def test_mock_analysis_grammar(self):
        text = "She don't like apples."
        # Call with context to ensure signature match
        result = asyncio.run(self.agent.analyze_turn(text, context="Previous turn info"))
        self.assertIsNotNone(result)
        self.assertEqual(result.category, AnalysisCategory.GRAMMAR)
        self.assertIn("doesn't", result.suggested_correction)

    def test_mock_analysis_sociolinguistics(self):
        text = "I'm gonna go to the store."
        # Call without context
        result = asyncio.run(self.agent.analyze_turn(text))
        self.assertIsNotNone(result)
        self.assertEqual(result.category, AnalysisCategory.SOCIOLINGUISTICS)
        self.assertIn("going to", result.suggested_correction)

    def test_no_analysis(self):
        text = "Hello world."
        result = asyncio.run(self.agent.analyze_turn(text))
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
