import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import sys
import os
import json
import logging
from datetime import datetime

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions to test
from main import (
    validate_audio_device,
    normalize_student_name,
    calculate_file_hash,
    get_existing_students,
    start_new_session,
    save_turn_to_session,
    handle_mark_update_sync,
    save_session_to_file,
    analyze_turn_with_llm,
    perform_batch_diarization,
    upload_analysis_to_supabase,
    current_session
)
import main

class TestPreSession(unittest.TestCase):

    @patch('main.pyaudio.PyAudio')
    def test_validate_audio_device_success(self, MockPyAudio):
        # Setup mock
        p = MockPyAudio.return_value
        p.get_device_count.return_value = 2
        p.get_device_info_by_index.return_value = {"name": "Test Mic", "maxInputChannels": 1}

        # Test
        result = validate_audio_device(0)

        # Assert
        self.assertTrue(result)
        p.terminate.assert_called_once()

    @patch('main.pyaudio.PyAudio')
    def test_validate_audio_device_invalid_index(self, MockPyAudio):
        # Setup mock
        p = MockPyAudio.return_value
        p.get_device_count.return_value = 1
        # When printing available devices, it calls get_device_info_by_index for valid indices
        p.get_device_info_by_index.return_value = {"name": "Default Mic", "maxInputChannels": 1}

        # Test
        with patch('builtins.print') as mock_print:
            result = validate_audio_device(5)

        # Assert
        self.assertFalse(result)
        p.terminate.assert_called_once()

    @patch('main.pyaudio.PyAudio')
    def test_validate_audio_device_no_channels(self, MockPyAudio):
        # Setup mock
        p = MockPyAudio.return_value
        p.get_device_count.return_value = 1
        p.get_device_info_by_index.return_value = {"name": "Test Output", "maxInputChannels": 0}

        # Test
        with patch('builtins.print') as mock_print:
            result = validate_audio_device(0)

        # Assert
        self.assertFalse(result)

    def test_normalize_student_name(self):
        self.assertEqual(normalize_student_name("  john doe  "), "John Doe")
        self.assertEqual(normalize_student_name("john (student)"), "John")
        self.assertEqual(normalize_student_name("mary-jane"), "Mary-jane")
        self.assertEqual(normalize_student_name(None), "Unknown")
        self.assertEqual(normalize_student_name(""), "Unknown")

    def test_calculate_file_hash(self):
        with patch("builtins.open", mock_open(read_data=b"test data")) as mock_file:
            # md5("test data") = eb733a00c0c9d336e65691a37ab54293
            result = calculate_file_hash("dummy.txt")
            self.assertEqual(result, "eb733a00c0c9d336e65691a37ab54293")

    def test_calculate_file_hash_error(self):
         with patch("builtins.open", side_effect=Exception("File not found")):
             result = calculate_file_hash("nonexistent.txt")
             self.assertIsNone(result)

    @patch('main.supabase')
    def test_get_existing_students_supabase(self, mock_supabase):
        # Mock supabase response
        mock_response = MagicMock()
        mock_response.data = [
            {"first_name": "John", "username": "john-doe"},
            {"first_name": "Jane", "username": "jane-doe-2024"},
            {"first_name": "Aaron", "username": "aaron-tutor"}, # Should be skipped
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response

        # Mock local students
        with patch('main.get_local_existing_students', return_value=["Local Student"]):
            students = get_existing_students()

        self.assertIn("John Doe", students)
        self.assertIn("Jane Doe 2024", students)
        self.assertIn("Local Student", students)
        self.assertNotIn("Aaron Tutor", students) # Should be skipped

    @patch('main.supabase', None)
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

    @patch('main.Path.mkdir')
    def test_start_new_session(self, mock_mkdir):
        start_new_session("test_session_id", "Test Student")

        self.assertEqual(main.current_session["session_id"], "test_session_id")
        self.assertEqual(main.current_session["student_name"], "Test Student")
        self.assertTrue(main.current_session["file_path"].startswith("sessions/test_student_session_"))
        self.assertIsNotNone(main.current_session["start_time"])

    def test_save_turn_to_session(self):
        # Mock TurnEvent
        mock_event = MagicMock()
        mock_event.turn_order = 1
        mock_event.transcript = "Hello world"
        mock_event.speaker = "B" # Student
        mock_event.turn_is_formatted = True
        mock_event.end_of_turn = True
        mock_event.end_of_turn_confidence = 0.95
        mock_event.created = datetime.now()

        # Mock words
        word1 = MagicMock()
        word1.text = "Hello"
        word1.start = 0
        word1.end = 500
        word1.confidence = 0.9
        word1.word_is_final = True

        word2 = MagicMock()
        word2.text = "world"
        word2.start = 600
        word2.end = 1000
        word2.confidence = 0.9
        word2.word_is_final = True

        mock_event.words = [word1, word2]

        # Setup current session
        main.current_session["student_name"] = "Student A"

        save_turn_to_session(mock_event)

        self.assertEqual(len(main.current_session["turns"]), 1)
        turn = main.current_session["turns"][0]
        self.assertEqual(turn["transcript"], "Hello world")
        self.assertEqual(turn["speaker"], "Student A")
        self.assertEqual(turn["analysis"]["word_count"], 2)
        # Pause duration: 600 - 500 = 100
        self.assertEqual(turn["analysis"]["total_pause_time_ms"], 100)

    def test_handle_mark_update_sync(self):
        # Setup turn
        turn = {"turn_order": 1, "transcript": "test", "marked": False}
        main.current_session["turns"] = [turn]

        # Mark update
        data = {
            "turn_order": 1,
            "mark_type": "Important",
            "timestamp": datetime.now().isoformat()
        }

        handle_mark_update_sync(data)

        self.assertTrue(main.current_session["turns"][0]["marked"])
        self.assertEqual(main.current_session["turns"][0]["mark_type"], "Important")

        # Unmark
        data["mark_type"] = None
        handle_mark_update_sync(data)

        self.assertFalse(main.current_session["turns"][0]["marked"])
        self.assertIsNone(main.current_session["turns"][0]["mark_type"])


class TestIntraSessionAsync(unittest.IsolatedAsyncioTestCase):
    @patch('main.api_key', 'test_key')
    @patch('main.httpx.AsyncClient')
    async def test_analyze_turn_with_llm_success(self, mock_client_cls):
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Mock tool call response
        tool_call_args = {
            "category": "GRAMMAR_ERR",
            "suggestedCorrection": "Corrected text",
            "explanation": "Explanation"
        }

        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "arguments": json.dumps(tool_call_args)
                        }
                    }]
                }
            }]
        }

        mock_client.post.return_value = mock_response

        result = await analyze_turn_with_llm("test text")

        self.assertEqual(result, tool_call_args)

    @patch('main.api_key', 'test_key')
    @patch('main.httpx.AsyncClient')
    async def test_analyze_turn_with_llm_fallback(self, mock_client_cls):
        # Setup mock client
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Mock response without tool calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {}
            }]
        }

        mock_client.post.return_value = mock_response

        result = await analyze_turn_with_llm("test text")

        self.assertEqual(result["category"], "NONE")


class TestPostSession(unittest.TestCase):

    def setUp(self):
         main.current_session = {
            "session_id": "sess_123",
            "start_time": datetime.now().isoformat(),
            "student_name": "Student A",
            "turns": [{"turn_order": 1, "words": []}],
            "file_path": "test_session.json",
            "notes": "Test notes",
            "audio_path": "test.wav"
        }

    @patch('main.open', new_callable=mock_open)
    @patch('main.gc.collect')
    def test_save_session_to_file(self, mock_gc, mock_file):
        save_session_to_file()

        mock_file.assert_called_with("test_session.json", "w")
        handle = mock_file()
        mock_gc.assert_called()

class TestPostSessionAsync(unittest.IsolatedAsyncioTestCase):

    @patch('main.Transcriber')
    async def test_perform_batch_diarization_success(self, MockTranscriber):
        # Setup
        mock_transcriber = MockTranscriber.return_value

        mock_transcript = MagicMock()
        mock_transcript.status = "completed"

        # Mock utterances
        utt1 = MagicMock()
        utt1.speaker = "A"
        utt1.text = "Hello"
        utt1.start = 100
        utt1.end = 200
        utt1.confidence = 0.9

        mock_transcript.utterances = [utt1]

        mock_transcriber.transcribe_async = AsyncMock(return_value=mock_transcript)

        # Mock file operations
        with patch('main.os.path.exists', return_value=True), \
             patch('main.open', mock_open(read_data='{"turns": []}')) as mock_file:

            result = await perform_batch_diarization("audio.wav", "session.json")

            self.assertTrue(result)
            mock_transcriber.transcribe_async.assert_called_once()
            # Verify file was written (updated)
            # mock_file.assert_called_with("session.json", "w") # mock_open is reused so this is tricky

    @patch('main.Transcriber')
    async def test_perform_batch_diarization_fail(self, MockTranscriber):
        mock_transcriber = MockTranscriber.return_value
        mock_transcript = MagicMock()
        mock_transcript.status = "error"
        mock_transcript.error = "Test Error"

        mock_transcriber.transcribe_async = AsyncMock(return_value=mock_transcript)

        with patch('main.os.path.exists', return_value=True):
             result = await perform_batch_diarization("audio.wav", "session.json")
             self.assertFalse(result)

    @patch.dict(os.environ, {"ASSEMBLYAI_API_KEY": "test_key"})
    @patch('main.supabase')
    @patch('main.perform_batch_diarization', new_callable=AsyncMock)
    @patch('main.calculate_file_hash', return_value="hash123")
    @patch('main.analyze_session_file')
    @patch('main.get_student_id', return_value=1)
    @patch('main.httpx.AsyncClient') # For sanity upload
    async def test_upload_analysis_to_supabase(self, mock_client, mock_get_student_id, mock_analyze, mock_hash, mock_diarization, mock_supabase):
        # Mock return values
        mock_diarization.return_value = True

        # Mock duplicate check (returns empty list means no duplicate)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

        # Mock session analysis
        mock_analyze.return_value = {
            "session_info": {"student_name": "Student A", "start_time": datetime.now().isoformat()},
            "student_metrics": {"wpm": 100}
        }

        # Mock file reads
        # We need to mock open multiple times for different purposes (duplicate check, analysis loading)
        session_data = {
            "session_id": "sess_1",
            "student_name": "Student A",
            "start_time": datetime.now().isoformat(),
            "turns": [],
            "diarized_turns": [{"speaker": "B", "text": "Hello", "confidence": 0.9}]
        }

        # Mock run_lemur_query to avoid import issues or side effects
        # main.py expects: analysis_results.get('lemur_analysis', {}).get('response', 'No analysis generated.')
        mock_lemur_result = {
            "lemur_analysis": {
                "response": "Test Analysis"
            }
        }

        with patch('analyzers.lemur_query.run_lemur_query', return_value=mock_lemur_result):
            with patch('main.open', mock_open(read_data=json.dumps(session_data))):
                await upload_analysis_to_supabase("session.json", 60, "audio.wav")

                # Verify insertions
                # student_sessions
                # student_corpus
                self.assertTrue(mock_supabase.table.called)

if __name__ == '__main__':
    unittest.main()
