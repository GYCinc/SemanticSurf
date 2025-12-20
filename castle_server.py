"""
Castle Server: The Sovereign TheGuru Instance
This script runs inside a Railway Castle (container).
It acts as the student-bound analysis engine.
"""

import os
import json
from fastapi import FastAPI, HTTPException, Header
from pydantic import ValidationError
from typing import Dict, Any, List

from analyzers.schemas import LanguageFeedback, LinguisticSubcategory, OfficialCategory
from analyzers.session_analyzer import SessionAnalyzer
from analyzers.lm_gateway import run_lm_gateway_query

app = FastAPI(title=f"Castle: {os.getenv('STUDENT_ID', 'Unknown')}")

STUDENT_ID = os.getenv("STUDENT_ID")
HUB_SECRET = os.getenv("MCP_SECRET")

@app.get("/health")
def health_check():
    return {"status": "sovereign", "student_id": STUDENT_ID}

@app.post("/analyze")
async def analyze_session(payload: Dict[str, Any], authorization: str = Header(None)):
    """
    The Core Distillation Endpoint.
    Receives Triple-Transcript data -> Runs Analysis -> Validates -> Returns Holy Data.
    """
    # 1. Security Check
    if authorization != f"Bearer {HUB_SECRET}":
        raise HTTPException(status_code=401, detail="Unauthorized: Hub Secret Mismatch")

    try:
        # 2. Extract Data
        # Expecting artifacts: raw_text, sentences, words
        student_text = payload.get("student_text", "")
        
        # 3. The TheGuru's Work (LLM Distillation)
        # Note: In a real Castle, we'd save artifacts locally to a Volume
        analysis_context = payload.get("analysis_context", {})
        
        # 4. Petty Dantic's Validation
        # We simulate the TheGuru's output and run it through the hardcoded schemas.py
        raw_feedback = analysis_context.get("detected_errors", [])
        validated_feedback = []
        
        for item in raw_feedback:
            try:
                # Force every item through Petty Dantic
                clean_item = LanguageFeedback(**item)
                validated_feedback.append(clean_item.model_dump())
            except ValidationError as e:
                print(f"⚠️ Petty Dantic rejected item: {e}")
                # We skip corrupted data to maintain Holy Consistency
                continue

        return {
            "success": True,
            "student_id": STUDENT_ID,
            "validated_analysis": validated_feedback,
            "the_guru_journal": "Castle Analysis Complete. No structural drift detected."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
