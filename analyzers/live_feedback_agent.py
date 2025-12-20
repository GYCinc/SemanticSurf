import json
import logging
import httpx
from typing import Any
from .schemas import OfficialCategory, LanguageFeedback
from dotenv import load_dotenv

_ = load_dotenv()
logger = logging.getLogger(__name__)

class LiveFeedbackAgent:
    """
    Real-time linguistic analysis for ESL tutoring sessions.
    
    Analyzes student turns during live sessions and returns structured feedback
    categorized into the 4 SLA domains (Phonology, Lexis, Syntax, Pragmatics),
    which get mapped to the 6 student-facing publicCategories.
    """

    api_key: str
    gateway_url: str

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.gateway_url = "https://llm-gateway.assemblyai.com/v1/chat/completions"

    async def analyze_turn(self, text: str, context: str = "") -> dict[str, Any]:
        """
        Analyzes a turn and returns a dictionary matching the LanguageFeedback schema.
        """
        if not self.api_key:
            return {"error": "Missing API Key"}

        # Define the tool for the LLM
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "submit_language_feedback",
                    "description": "Submit structured feedback for a language learner.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": [e.value for e in OfficialCategory],
                                "description": "The category of the linguistic issue."
                            },
                            "suggestedCorrection": {
                                "type": "string",
                                "description": "The natural, corrected version of the sentence."
                            },
                            "explanation": {
                                "type": "string",
                                "description": "A concise explanation of the error (max 2 sentences)."
                            },
                            "detectedTrigger": {
                                "type": "string",
                                "description": "The specific text that caused the issue."
                            }
                        },
                        "required": ["category", "suggestedCorrection", "explanation"]
                    }
                }
            }
        ]

        payload = {
            "model": "claude-3-5-haiku-20241022",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert ESL tutor. Analyze the last user utterance given the context. Use the 'submit_language_feedback' tool to provide your analysis. If there are no issues, use category 'Pragmatics' or 'Lexis' to give positive reinforcement or return nothing."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nStudent Utterance: \"{text}\""
                }
            ],
            "max_tokens": 1000,
            "tools": tools,
            "tool_choice": {"type": "function", "function": {"name": "submit_language_feedback"}}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.gateway_url, headers={"authorization": self.api_key, "content-type": "application/json"}, json=payload, timeout=15.0)
                response.raise_for_status()
                _ = response # Mark as used
                result = response.json()

                try:
                    choice = result["choices"][0]
                    if choice["message"].get("tool_calls"):
                        tool_call = choice["message"]["tool_calls"][0]
                        args = json.loads(tool_call["function"]["arguments"])

                        # --- PETTY DANTIC VALIDATION ---
                        # Validate against our Pydantic schema
                        feedback = LanguageFeedback(**args)
                        return feedback.model_dump(mode='json', by_alias=True)
                    else:
                        return {"category": "Pragmatics", "suggestedCorrection": text, "explanation": "No specific feedback generated."}

                except Exception as e:
                    logger.error(f"Validation or Parsing Error: {e}")
                    return {"error": "Analysis failed validation"}

        except Exception as e:
            logger.error(f"LLM Gateway Error: {e}")
            return {"error": str(e)}
