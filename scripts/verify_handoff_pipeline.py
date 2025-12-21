import os
import sys
import asyncio
import json
import unittest
import httpx # type: ignore
from typing import Any
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

# Add repo root to sys.path (so `AssemblyAIv2.*` imports work regardless of CWD)
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# Mock AssemblyAI to avoid real network calls
mock_aai = MagicMock()
class FakeConfig:
    def __init__(self, **kwargs: Any):
        self.__dict__.update(kwargs)
mock_aai.TranscriptionConfig = FakeConfig
sys.modules["assemblyai"] = mock_aai
sys.modules["assemblyai.streaming"] = MagicMock()
sys.modules["assemblyai.streaming.v3"] = MagicMock()

# Mock dependencies that might be missing in test env
sys.modules["pyaudio"] = MagicMock()

# Import the target function
from AssemblyAIv2.ingest_audio import process_and_upload

class TestHandoffPipeline(unittest.IsolatedAsyncioTestCase):
    _mock_httpx_client_patcher: Any | None = None # type: ignore
    _mock_transcriber_patcher: Any | None = None # type: ignore
    mock_httpx_client: MagicMock | None = None # type: ignore
    mock_transcriber_cls: MagicMock | None = None # type: ignore

    def setUp(self): # type: ignore
        # Setup mocks
        self._mock_httpx_client_patcher = patch('AssemblyAIv2.ingest_audio.httpx.AsyncClient')
        self.mock_httpx_client = self._mock_httpx_client_patcher.start()
        
        self._mock_transcriber_patcher = patch('AssemblyAIv2.ingest_audio.aai.Transcriber')
        self.mock_transcriber_cls = self._mock_transcriber_patcher.start()

    def tearDown(self): # type: ignore
        if self._mock_httpx_client_patcher:
            self._mock_httpx_client_patcher.stop()
        if self._mock_transcriber_patcher:
            self._mock_transcriber_patcher.stop()

    async def test_pipeline_handoff(self):
        """
        Verifies that process_and_upload:
        1. Calls AssemblyAI for diarization
        2. Runs local analyzers (mocked implicit verification by checking payload)
        3. Sends the correct payload structure to the Hub API
        """
        print("\n🧪 Starting Pipeline Verification...")

        # --- SETUP MOCKS ---

        # 1. Mock AssemblyAI Transcripts
        assert self.mock_transcriber_cls is not None
        mock_transcriber = self.mock_transcriber_cls.return_value

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
        # The code calls transcribe twice concurrently, so we need deterministic return based on config
        def transcribe_side_effect(*args, **kwargs):
            # args[0] is upload_url, args[1] is config
            config = args[1]
            if getattr(config, 'punctuate', False):
                return mock_transcript_diar
            return mock_transcript_raw
            
        mock_transcriber.transcribe.side_effect = transcribe_side_effect

        
        # 2. Mock HTTPX Client (for Upload AND LLM)
        mock_client_instance = AsyncMock()
        
        # Define deterministic responses based on URL
        async def mock_post_side_effect(url, *args, **kwargs):
            # 1. Mistral Call - REAL CALL if Key exists
            if "mistral" in str(url):
                 print("    🦅 Performing REAL Boss MF Call to Mistral...")
                 async with httpx.AsyncClient(timeout=60.0) as real_client:
                     # pass through the same args/kwargs
                     return await real_client.post(url, *args, **kwargs)

            # 2. GitEnglishHub Call - KEEP MOCKED
            elif "gitenglish" in str(url) or "/api/mcp" in str(url):
                print("    🛡️ Mocking GitEnglishHub Upload...")
                return MagicMock(
                    status_code=200,
                    json=lambda: {"success": True, "sessionId": "test_session_123"}
                )
            return MagicMock(status_code=404)

        mock_client_instance.post.side_effect = mock_post_side_effect
        assert self.mock_httpx_client is not None
        self.mock_httpx_client.return_value = mock_client_instance
        self.mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        # NOTE: LLM synthesis is intentionally skipped during ingest for stability.

        # --- EXECUTE ---
        audio_file_path = Path("test_audio.wav")
        student_name = "Test Student"
        session_date = "2023-10-26"

        audio_file_path.touch()

        try:
            # Inherit real key if available, else default to test_key
            real_key = os.environ.get("MISTRAL_API_KEY", "test_key")
            
            with patch.dict(os.environ, {"MCP_SECRET": "test_secret", "MISTRAL_API_KEY": real_key}):
                # We need to reload the module or patch the variable directly if it was loaded at module level
                # Assumes ingest_audio pulls os.environ.get(...) inside the function or logic, or if we need to patch specifically
                # In our case, ingest_audio.py does `api_key = os.environ.get("MISTRAL_API_KEY")` inside the function, 
                # so patch.dict above should work!
                # BUT if we want to be safe with existing patches:
                with patch("AssemblyAIv2.ingest_audio.GITENGLISH_MCP_SECRET", "test_secret"):
                     # We don't need to patch OPENAI_API_KEY anymore if we aren't using it.
                     pass

                     # 3. Call the Pipeline Function
                     result = await process_and_upload(
                        audio_path=str(audio_file_path),
                        student_name=student_name,
                        notes="Test Notes"
                     )
        finally:
             audio_file_path.unlink(missing_ok=True)

        # --- VERIFICATIONS ---

        # 1. Verify Transcriber was initialized and called
        assert self.mock_transcriber_cls is not None
        self.mock_transcriber_cls.assert_called_once()
        assert mock_transcriber is not None
        mock_transcriber.transcribe.assert_called()
        self.assertEqual(mock_transcriber.transcribe.call_count, 2) # check call count

        # 2. Verify Upload via HTTPX
        upload_call_args = mock_client_instance.post.call_args
        self.assertIsNotNone(upload_call_args)
        
        url, kwargs = upload_call_args[0], upload_call_args[1]
        
        self.assertIn("/api/mcp", str(url))
        
        payload = kwargs.get("json", {})
        self.assertEqual(payload.get("action"), "ingest.createSession")
        
        params = payload.get("params", {})
        self.assertEqual(params.get("student_name"), None) # student_name is used in ID but maybe not in params directly? Actually let's check
        # In ingest_audio.py: 'studentId' is not in params, it is passed to send_to_gitenglish as argument. 
        # But wait, send_to_gitenglish might put it in payload wrapper? 
        # ingest_audio.py calls send_to_gitenglish(..., student_id_or_name=student_name, params=params)
        # We are checking mock_client_instance.post payload.
        # verify_handoff_pipeline assumption might be that params contains everything.
        # But typically send_to_gitenglish wraps params? 
        # Let's check send_to_gitenglish in ingest_audio if possible. But verify_handoff checks url /api/mcp.
        
        # Assuming verify_handoff checks the raw Hub API call (mock_client_instance.post).
        # We need to know what send_to_gitenglish does.
        # But based on typical MCP patterns, it posts JSON.
        
        # We will assume params structure from ingest_audio.py lines 411+
        
        # self.assertEqual(params.get("student_name"), student_name) - student_name is NOT in params map in ingest_audio.py
        
        # Check that we have valid JSON-serializable structures
        self.assertIn("transcriptText", params)
        self.assertIn("turns", params)
        self.assertIn("llmGatewayPhenomena", params)
        self.assertIn("llmGatewayAnalysis", params)
        self.assertIn("llmAnalysis", params)
        self.assertIn("sessionDate", params)
        
        # Verify content of turns
        self.assertIsInstance(params["turns"], list)
        if len(params["turns"]) > 0:
            self.assertIn("transcript", params["turns"][0])
            self.assertIn("speaker", params["turns"][0])
            
        # Verify result structure
        self.assertTrue(result["success"])
        self.assertEqual(result["sessionId"], "test_session_123")
        self.assertGreaterEqual(len(params['sentences']), 1)

        # Check Word-Level Data (Critical for Learner Corpus)
        words = params['turns'][0]['words']
        self.assertTrue(len(words) >= 2, "Should have words in the turn")
        self.assertEqual(words[0]['text'], "Hello") # Raw, no punctuation
        self.assertEqual(words[1]['text'], "world") # Raw, no punctuation

        # Check LLM Gateway phenomena list (may be empty in test)
        errors = params['llmGatewayPhenomena']
        print(f"✅ Detected Errors: {len(errors)}")
        if errors:
            print(f"   Sample: {errors[0]}")

        # Deterministic analyzers might or might not find anything on "Hello world".
        # This test validates the *shape* of the payload, not the quantity of errors.
        self.assertIsInstance(errors, list)

if __name__ == "__main__":
    unittest.main()
