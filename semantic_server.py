from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import logging
import json
from analyzers.llm_gateway import generate_analysis
from analyzers.schemas import Turn

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SemanticServer")

app = FastAPI(title="Semantic Server (MiniGuru)", version="2.0.0")

class AnalysisRequest(BaseModel):
    student_name: str
    transcript_text: str
    turns: list[Turn] # Raw turns or simplified
    system_prompt: str | None = None

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Semantic Server", "version": "2.0.0"}

@app.post("/analyze")
async def analyze_session(request: AnalysisRequest):
    """
    The Polyguru Endpoint: Analyzes a session using the LLM Gateway.
    """
    logger.info(f"🧠 Analysis requested for student: {request.student_name}")

    # --- 1. LOCAL ANALYSIS (The Deterministic Layer) ---
    logger.info("⚙️ Running Local Analysis Suite...")
    local_insights = {
        "metrics": {},
        "phenomena": [],
        "fluency": {},
        "register": {},
        "grammar_checks": {}
    }
    
    try:
        # Prepare data structure for SessionAnalyzer
        session_data = {
            "turns": [t.dict() for t in request.turns] if request.turns else [],
            "transcript": request.transcript_text,
            "student_name": request.student_name,
            "speaker_map": {"A": request.student_name, "B": "Tutor"} # Assumption for now
        }
        
        # 1.1 Session & Metrics (Core CAF)
        from analyzers.session_analyzer import SessionAnalyzer
        core_analyzer = SessionAnalyzer(session_data)
        local_insights["metrics"] = core_analyzer.analyze_all()
        student_text = core_analyzer.student_full_text

        # 1.2 Phenomena Matcher (Static Patterns)
        from analyzers.phenomena_matcher import ErrorPhenomenonMatcher
        matcher = ErrorPhenomenonMatcher()
        await matcher.initialize()
        local_insights["phenomena"] = matcher.match(student_text)

        # 1.3 Fluency Analysis (Timing/Hesitation)
        from analyzers.fluency_analyzer import FluencyAnalyzer
        fluency = FluencyAnalyzer()
        # Extract word timing from turns if available
        # This assumes Turns provided in request have word-level data
        all_words = []
        for turn in request.turns:
            if hasattr(turn, 'words') and turn.words:
                all_words.extend([w.dict() if hasattr(w, 'dict') else w for w in turn.words])
        if all_words:
            local_insights["fluency"] = fluency.analyze_hesitation(all_words)

        # 1.4 Register & Genre (Amalgum)
        from analyzers.amalgum_analyzer import AmalgumAnalyzer
        amalgum = AmalgumAnalyzer()
        local_insights["register"] = {
            "scores": amalgum.analyze_register(student_text),
            "classification": amalgum.get_genre_classification(student_text)
        }

        # 1.5 Granular Grammar Checks
        from analyzers.article_analyzer import ArticleAnalyzer
        from analyzers.preposition_analyzer import PrepositionAnalyzer
        from analyzers.learner_error_analyzer import LearnerErrorAnalyzer
        
        local_insights["grammar_checks"] = {
            "articles": ArticleAnalyzer().analyze(student_text),
            "prepositions": PrepositionAnalyzer().analyze(student_text),
            "learner_errors": LearnerErrorAnalyzer().analyze(student_text)
        }

        logger.info(f"✅ Local Suite Complete. Register: {local_insights['register']['classification']}")

    except Exception as e:
        logger.error(f"❌ Local Analysis Failed: {e}")
        local_insights["error"] = str(e)

    # --- 2. LLM GATEWAY (The Reasoning Layer) ---
    logger.info("🦅 Calling LLM Gateway with Grounded Context...")
    
    # Construct High-Fidelity Context for LLM
    user_message = f"""
SESSION ANALYSIS REQUEST: {request.student_name}

[LAYER 1: RAW TRANSCRIPT]
{request.transcript_text}

[LAYER 2: DETERMINISTIC LINGUISTIC DATA]
- Overall Status: {local_insights.get('register', {}).get('classification', 'Standard')} Register Detected.
- Fluency: {local_insights.get('fluency', {}).get('hesitation_count', 0)} hesitations identified.
- Grammar Matches: {len(local_insights.get('grammar_checks', {}).get('learner_errors', []))} high-confidence learner patterns.
- Specific Patterns: {', '.join([p['item'] for p in local_insights.get('phenomena', [])[:5]]) if local_insights.get('phenomena') else 'None detected by rule-base'}

[DETAILED LOCAL METRICS]
{json.dumps(local_insights, indent=2, default=str)}

INSTRUCTIONS: 
Combine the local linguistic data with your own deep reasoning to generate a definitive post-lesson report.
Ensure you cross-reference the 'phenomena' found by the local matcher.
"""

    system_prompt = request.system_prompt
    if not system_prompt:
        try:
            with open("UNIVERSAL_GURU_PROMPT.txt", "r") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            system_prompt = "You are an expert ESL linguistic analyst."

    try:
        llm_result = await generate_analysis(
            system_prompt=system_prompt,
            user_message=user_message,
            model="gemini-3-flash-preview"
        )

        return {
            "student": request.student_name,
            "local_analysis": local_insights,
            "llm_analysis": llm_result
        }
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. OPTIONAL CALENDAR INTEGRATION ---
@app.post("/calendar/create-event")
async def create_event(summary: str, description: str, start_time: str, end_time: str):
    """
    Standalone Calendar Endpoint for Semantic Server.
    Only functional if Google credentials are provided.
    """
    try:
        from lib.calendar_client import create_calendar_event
        result = create_calendar_event(summary, description, start_time, end_time)
        if not result:
             raise HTTPException(status_code=503, detail="Google Calendar not configured or not authenticated (token.json missing)")
        return {"success": True, "event": result}
    except ImportError:
        raise HTTPException(status_code=501, detail="Calendar client not implemented")
    except Exception as e:
        logger.error(f"📅 Calendar event creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/next")
async def get_next_lesson():
    """
    Retrieves the next lesson to enable auto-booting or context awareness.
    """
    try:
        from lib.calendar_client import get_next_event
        events = get_next_event()
        if events is None:
             # Return empty list instead of 503 to avoid breaking clients that just want to check
             return {"events": [], "status": "not_configured"}
        return {"events": events, "status": "ok"}
    except ImportError:
        return {"events": [], "status": "no_client"}
    except Exception as e:
        logger.error(f"📅 Calendar fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
