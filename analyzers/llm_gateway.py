"""
LLM Gateway: The Bridge to The Castle
Client-side logic that pushes analysis data from Semantic Surfer (AssemblyAIv2)
to the GitEnglishHub (The Castle) via the Petty Dantic API.
"""

import os
import json
import httpx
import logging
from typing import Any
from .schemas import Turn

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LLMGateway")

# Configuration
GITENGLISH_API_BASE = os.getenv("GITENGLISH_API_BASE", "https://gitenglish.com")
MCP_SECRET = os.getenv("MCP_SECRET")

def push_to_semantic_server(
    student_name: str,
    turns: list[Turn], 
    analysis_context: dict[str, Any],
    session_id: str | None = None,
    notes: str = ""
) -> dict[str, Any]:
    """
    The Handoff: Pushes local analysis data to the Central Castle (GitEnglishHub).
    
    Args:
        student_name: Name of the student.
        turns: List of Turn objects from the session.
        analysis_context: Dictionary of linguistic analysis (from local agents).
        session_id: The specific session ID (mapped to AssemblyAI transcript ID if possible).
        notes: Teacher notes.
        
    Returns:
        JSON response from the Castle API.
    """
    if not MCP_SECRET:
        logger.error("❌ MCP_SECRET is missing! Cannot authenticate with The Castle.")
        return {"success": False, "error": "MCP_SECRET missing"}

    url = f"{GITENGLISH_API_BASE}/api/mcp"
    
    # 1. Construct the Holy Payload (Petty Dantic compliant)
    # Note: We must serialize Turn objects to dicts
    serializable_turns = [t.model_dump() for t in turns]
    
    payload = {
        "action": "sanity.createLessonAnalysis", # Direct mapping to Hub action
        "studentId": student_name, # Student identifier for the session
        "params": {
            "studentName": student_name,
            "sessionDate": turns[0].timestamp if turns else None,
            "analysisReport": json.dumps(analysis_context, default=str), # Raw context for context.
            "teacherNotes": notes,
            "transcriptId": session_id,
            "rawTurns": serializable_turns,
             # We include the raw linguistic findings so the Hub can curate them
            "detectedPhenomena": analysis_context.get("detected_errors", []) 
        }
    }
    
    headers = {
        "Authorization": f"Bearer {MCP_SECRET}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"🚀 Pushing data to GitEnglishHub: {url}")
    logger.info(f"   Student: {student_name}")
    logger.info(f"   Turns: {len(serializable_turns)}")

    try:
        # 2. Execute the Push
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info("✅ Data handed off to GitEnglishHub successfully.")
            return data

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ GitEnglishHub Rejected Data (HTTP {e.response.status_code}): {e.response.text}")
        return {"success": False, "error": f"HTTP {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        logger.error(f"❌ Handoff Failed: {e}")
        return {"success": False, "error": str(e)}

# Alias for backward compatibility
run_lm_gateway_query = push_to_semantic_server

if __name__ == '__main__':
    # Standalone Test
    print("Testing Handoff...")
    # Mock data
    mock_turns = [
        Turn(turn_order=1, transcript="Hello", speaker="Tutor", timestamp="2024-01-01T12:00:00"),
        Turn(turn_order=2, transcript="Hi teacher", speaker="Student", timestamp="2024-01-01T12:00:05")
    ]
    res = push_to_semantic_server("Test Student", mock_turns, {"detected_errors": []}, "test_session_123")
    print(json.dumps(res, indent=2))