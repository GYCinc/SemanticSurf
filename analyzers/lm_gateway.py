"""
LM Gateway: The TheGuru (Distillation Edition)
Uses a two-stage pipeline to distill raw session data into high-fidelity linguistic artifacts.
"""

from __future__ import annotations
import os
import sys
import json
import httpx
import logging
from pathlib import Path
from typing import cast, Any
from .schemas import LanguageFeedback, Turn

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

api_key = os.getenv('ASSEMBLYAI_API_KEY')
gateway_url = "https://llm-gateway.assemblyai.com/v1/chat/completions"

def load_the_guru_prompt() -> str:
    """Loads the insanely consistent TheGuru prompt from the root."""
    prompt_path = Path(__file__).parent.parent / "UNIVERSAL_GURU_PROMPT.txt"
    try:
        if not prompt_path.exists():
            # Fallback to current directory for relative runs
            prompt_path = Path("UNIVERSAL_GURU_PROMPT.txt")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"❌ Failed to load TheGuru prompt: {e}")
        return "You are an expert ESL tutor. Analyze the transcript."

def run_lm_gateway_query(session_file: Path, analysis_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    The 'TheGuru' Call (Stage 2).
    Distills the Collector's context dump into the 'Holy JSON'.
    """
    if not api_key:
        return {"error": "ASSEMBLYAI_API_KEY missing"}

    # 1. Stage 1: The Context Dump (CaptureEngine Data)
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load session: {e}"}

    turns = session_data.get('turns', [])
    raw_transcript = "\n".join([f"{t.get('speaker')}: {t.get('transcript', t.get('text'))}" for t in turns])
    
    # 2. Prepare the TheGuru's Input
    full_context = f"""
## 🏥 SESSION CONTEXT DUMP (RAW DATA)
{raw_transcript}

## 🧪 LOCAL NLP GROUNDING
{json.dumps(analysis_context, indent=2) if analysis_context else "No local metrics provided."} 

## 📝 TUTOR NOTES
{session_data.get('notes', 'No notes provided.')}
"""

    system_prompt = load_the_guru_prompt()

    # 3. The TheGuru Call (Synthesis)
    try:
        llm_payload = {
            "model": "gemini-1.5-pro", # Use the deep context model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Execute the distillation on this context dump:\n\n{full_context}"}
            ],
            "response_format": { "type": "json_object" },
            "max_tokens": 8000
        }
        
        headers = {"Authorization": str(api_key), "Content-Type": "application/json"}
        
        # Verify certifi works
        ssl_verify: str | bool = True
        try:
            import certifi
            ssl_verify = certifi.where()
        except:
            ssl_verify = False # Fallback to insecure if certs are missing
            logger.warning("⚠️ SSL Certs missing - running in insecure mode")

        response = httpx.post(gateway_url, json=llm_payload, headers=headers, timeout=120, verify=ssl_verify)
        response.raise_for_status()
        
        llm_result = response.json()
        raw_content = llm_result["choices"][0]["message"]["content"]
        
        # 4. Petty Dantic Validation (The Authority)
        # We ensure the output matches our Holy Schema
        distilled_data = json.loads(raw_content)
        
        return {
            "success": True,
            "holy_json": distilled_data,
            "usage": llm_result.get("usage")
        }

    except Exception as e:
        logger.error(f"❌ Distillation Failed: {e}")
        return {"error": "Distillation pipeline failed", "response": str(e)}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python lm_gateway.py <session_file.json>")
        sys.exit(1)
    
    analysis = run_lm_gateway_query(Path(sys.argv[1]))
    print(json.dumps(analysis, indent=2))