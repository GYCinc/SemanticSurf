import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import json

# Add repo root to sys.path
sys.path.append(os.getcwd())

# Mock AssemblyAI to avoid real network calls
sys.modules["assemblyai"] = MagicMock()
sys.modules["assemblyai.streaming"] = MagicMock()
sys.modules["assemblyai.streaming.v3"] = MagicMock()

# Mock dependencies that might be missing in test env
sys.modules["pyaudio"] = MagicMock()

# Import the target function
from ingest_audio import process_and_upload

class TestHandoffPipeline(unittest.IsolatedAsyncioTestCase):

    @patch("ingest_audio.aai.Transcriber")
    @patch("ingest_audio.httpx.AsyncClient")
    @patch("analyzers.llm_gateway.run_lm_gateway_query") # Mock LLM to speed up test
    async def test_pipeline_handoff(self, mock_llm_gateway, mock_httpx_client, mock_transcriber_cls):
        """
        Verifies that process_and_upload:
        1. Calls AssemblyAI for diarization
        2. Runs local analyzers (mocked implicit verification by checking payload)
        3. Sends the correct payload structure to the Hub API
        """
        print("\n🧪 Starting Pipeline Verification...")

        # --- SETUP MOCKS ---

        # 1. Mock AssemblyAI Transcripts
        mock_transcriber = mock_transcriber_cls.return_value

        # Mock Diarization Transcript (Pass 1)
        mock_utt = MagicMock()
        mock_utt.text = "Hello world."
        mock_utt.speaker = "A"
        mock_utt.words = [
            MagicMock(text="Hello", start=0, end=500, confidence=0.9),
            MagicMock(text="world", start=500, end=1000, confidence=0.9)
        ]

        # Mock Sentences
        mock_sentence = MagicMock()
        mock_sentence.text = "Hello world."
        mock_sentence.start = 0
        mock_sentence.end = 1000

        mock_transcript_diar = MagicMock()
        mock_transcript_diar.status = "completed"
        mock_transcript_diar.utterances = [mock_utt]
        mock_transcript_diar.text = "Hello world."
        mock_transcript_diar.get_sentences.return_value = [mock_sentence]

        # Mock Raw Transcript (Pass 2)
        mock_transcript_raw = MagicMock()
        mock_transcript_raw.status = "completed"
        mock_transcript_raw.words = [
            MagicMock(text="Hello", start=0, end=500, confidence=0.9),
            MagicMock(text="world", start=500, end=1000, confidence=0.9)
        ]
        mock_transcript_raw.audio_duration = 10.0

        # Configure transcribe side_effect for gather
        # The code calls transcribe twice concurrently
        mock_transcriber.transcribe.side_effect = [mock_transcript_diar, mock_transcript_raw]

        # 2. Mock HTTPX Client for Handoff
        # The key is that the method called on the client must be awaitable and return the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "sessionId": "test_session_123"}

        mock_post = AsyncMock(return_value=mock_response)

        mock_client_instance = AsyncMock()
        mock_client_instance.post = mock_post
        mock_client_instance.__aenter__.return_value = mock_client_instance

        # When AsyncClient() is called, return the context manager that yields the client
        mock_httpx_client.return_value = mock_client_instance

        # 3. Mock LLM Gateway
        mock_llm_gateway.return_value = {
            "lm_analysis": {
                "response": "Test LLM Analysis",
                "annotated_errors": [
                    {"quote": "Hello world", "correction": "Hello, world!", "explanation": "Test explanation"}
                ]
            }
        }

        # --- EXECUTE ---
        # Create a dummy audio file
        Path("test_audio.wav").touch()

        try:
            with patch.dict(os.environ, {"MCP_SECRET": "test_secret"}):
                # We need to reload the module or patch the variable directly if it was loaded at module level
                # ingest_audio.GITENGLISH_MCP_SECRET is a module-level variable loaded at start
                with patch("ingest_audio.GITENGLISH_MCP_SECRET", "test_secret"):
                   await process_and_upload("test_audio.wav", "Test Student", "Test Notes")
        finally:
             Path("test_audio.wav").unlink(missing_ok=True)

        # --- VERIFY ---

        # Check AssemblyAI calls
        self.assertEqual(mock_transcriber.transcribe.call_count, 2, "Should call transcribe twice (Dual Pass)")

        # Check Handoff Payload
        self.assertEqual(mock_post.call_count, 1, "Should call Hub API once")

        call_args = mock_post.call_args
        url = call_args[0][0]
        kwargs = call_args[1]
        payload = kwargs['json']

        print(f"\n✅ Handoff URL: {url}")
        print(f"✅ Payload Keys: {list(payload.keys())}")

        # Assertions on Payload
        self.assertEqual(payload['action'], 'ingest.createSession')
        self.assertEqual(payload['studentId'], 'Test Student')

        params = payload['params']
        self.assertIn('turns', params)
        self.assertIn('transcriptText', params)
        self.assertIn('punctuatedTranscript', params)
        self.assertIn('sentences', params)
        self.assertIn('errorPhenomena', params)
        self.assertIn('lmAnalysis', params)

        # Check specific content
        self.assertEqual(params['notes'], "Test Notes")
        self.assertEqual(len(params['turns']), 1)
        self.assertEqual(params['turns'][0]['transcript'], "Hello world")
        self.assertEqual(params['punctuatedTranscript'], "Hello world.")
        self.assertEqual(len(params['sentences']), 1)

        # Check Word-Level Data (Critical for Learner Corpus)
        words = params['turns'][0]['words']
        self.assertTrue(len(words) >= 2, "Should have words in the turn")
        self.assertEqual(words[0]['text'], "Hello") # Raw, no punctuation
        self.assertEqual(words[1]['text'], "world") # Raw, no punctuation

        # Check Error Phenomena (Merged from LLM + Rule Based)
        # Note: Rule based might find nothing on "Hello world", but LLM mock had one.
        errors = params['errorPhenomena']
        print(f"✅ Detected Errors: {len(errors)}")
        if errors:
            print(f"   Sample: {errors[0]}")

        self.assertGreaterEqual(len(errors), 1)
        self.assertEqual(errors[0]['source'], "LLM_ANALYSIS")

if __name__ == "__main__":
    unittest.main()
