import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from analyzers.material_agent import MaterialAgent
from schemas import AnalysisCategory

class TestMaterialAgent(unittest.TestCase):
    def setUp(self):
        self.agent = MaterialAgent(api_key="test_key")

    @patch("analyzers.material_agent.httpx.AsyncClient")
    def test_analyze_turn_success(self, mock_client_cls):
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "arguments": '{"category": "Vocabulary", "suggestedCorrection": "better word", "explanation": "Use better word", "detectedTrigger": "bad word"}'
                        }
                    }]
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()

        # Mock context manager
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Run test
        result = asyncio.run(self.agent.analyze_turn("test text"))

        self.assertEqual(result["category"], "Vocabulary")
        self.assertEqual(result["suggestedCorrection"], "better word")

    @patch("analyzers.material_agent.httpx.AsyncClient")
    def test_analyze_turn_no_feedback(self, mock_client_cls):
        # Mock response with no tool calls
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {}
            }]
        }
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = asyncio.run(self.agent.analyze_turn("perfect text"))

        self.assertEqual(result["category"], "Flow")

if __name__ == "__main__":
    unittest.main()
