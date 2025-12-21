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

# Import functions to test
from AssemblyAIv2.main import (
    get_existing_students,
    current_session
)
from AssemblyAIv2.ingest_audio import calculate_file_hash
import AssemblyAIv2.main as main

class TestPreSession(unittest.TestCase):

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

    @patch('main.os.path.exists', return_value=True)
    @patch('main.Path.glob')
    def test_get_existing_students_local(self, mock_glob, mock_exists):
        # Setup mock files
        mock_file1 = MagicMock()
        mock_file1.read_text.return_value = '{"student_name": "Alice"}'

        mock_file2 = MagicMock()
        mock_file2.read_text.return_value = '{"student_name": "Bob"}'

        mock_glob.return_value = [mock_file1, mock_file2]

        students = get_existing_students()

        self.assertEqual(students, ["Alice", "Bob"])

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
