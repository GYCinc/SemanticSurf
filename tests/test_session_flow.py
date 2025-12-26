import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import sys
import os
import json
import logging
from datetime import datetime

# Add parent directory to path to import main
# Add parent directory of the project to path to allow 'from AssemblyAIv2 import ...'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock assemblyai BEFORE importing main to avoid Pydantic/Config errors
mock_aai = MagicMock()
sys.modules["assemblyai"] = mock_aai
sys.modules["assemblyai.streaming"] = mock_aai
sys.modules["assemblyai.streaming.v3"] = mock_aai

# Mock internal dependencies that cause relative import issues
mock_analyzers = MagicMock()
sys.modules["AssemblyAIv2.analyzers"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.llm_gateway"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.schemas"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.session_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.sentence_chunker"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.lexical_engine"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.pos_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.ngram_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.verb_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.article_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.amalgum_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.comparative_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.phenomena_matcher"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.preposition_analyzer"] = mock_analyzers
sys.modules["AssemblyAIv2.analyzers.learner_error_analyzer"] = mock_analyzers

# Import functions to test
from AssemblyAIv2.main import (
    get_existing_students,
    current_session
)
from AssemblyAIv2.upload_audio_aai import calculate_file_hash
import AssemblyAIv2.main as main

class TestPreSession(unittest.IsolatedAsyncioTestCase):

    # Removed: validate_audio_device, normalize_student_name logic moved or deleted.

    def test_calculate_file_hash(self):
        with patch("builtins.open", mock_open(read_data=b"test data")) as mock_file:
            # md5("test data") = eb733a00c0c9d336e65691a37ab54293
            result = calculate_file_hash("dummy.txt")
            self.assertEqual(result, "eb733a00c0c9d336e65691a37ab54293")

    def test_calculate_file_hash_error(self):
         with patch("builtins.open", side_effect=Exception("File not found")):
             result = calculate_file_hash("nonexistent.txt")
             self.assertIsNone(result)

    @patch('AssemblyAIv2.main.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='["Alice", "Bob"]')
    async def test_get_existing_students_local(self, mock_open, mock_exists):
        students = await get_existing_students()
        self.assertEqual(students, ["Alice", "Bob", "System Test Student"])

class TestIntraSession(unittest.TestCase):
    def setUp(self):
        # Reset current_session before each test
        main.current_session = {
            "session_id": None,
            "start_time": None,
            "student_name": "Unknown",
            "turns": [],
            "file_path": None,
            "notes": "",
            "audio_path": None
        }

    # Removed: start_new_session, save_turn_to_session (logic partially integrated into event handlers)

# Removed: TestIntraSessionAsync (analyze_turn_with_llm moved to lm_gateway)



if __name__ == '__main__':
    unittest.main()
