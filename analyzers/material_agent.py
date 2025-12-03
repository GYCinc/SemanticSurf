import asyncio
import os
import json
import logging
from typing import Optional
import openai
from schemas import LanguageFeedback, AnalysisCategory

logger = logging.getLogger("MaterialAgent")

class MaterialAgent:
    def __init__(self, api_key: str = None):
        # Allow api_key injection or env var fallback
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. Analysis will fail silently.")
        else:
            openai.api_key = self.api_key

        self.system_prompt = """
You are an expert ESL linguistic analyst assisting a tutor in real-time.
Your goal is to identify ONE critical linguistic improvement in the student's speech.
Focus on these categories: Phrasal Verbs, Vocabulary, Expressions, Grammar, Pronunciation, Flow, Discourse, Sociolinguistics.

Output valid JSON matching this schema:
{
  "category": "Grammar",
  "suggestedCorrection": "Corrected sentence here.",
  "explanation": "Brief explanation of why.",
  "detected_trigger": "The phrase that triggered this."
}

If the speech is correct or trivial (e.g. "Yes", "Hello"), return null or an empty object.
Avoid nitpicking. Focus on intermediate/advanced errors or improvements.
"""

    async def analyze_turn(self, text: str, context: str = "") -> Optional[LanguageFeedback]:
        """
        Analyzes the text using an LLM to produce structured feedback.
        Accepts 'context' to match the calling signature in main.py, though currently unused.
        """
        if not self.api_key or len(text.split()) < 3:
            return None

        try:
            # Check for mock mode (used in tests or dev without keys)
            if self.api_key == "mock":
                return self._mock_analysis(text)

            # Construct the prompt with context if available
            user_content = text
            if context:
                user_content = f"Context:\n{context}\n\nCurrent Turn:\n{text}"

            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=150,
                response_format={ "type": "json_object" }
            )

            content = response.choices[0].message.content
            if not content: return None

            data = json.loads(content)
            if not data or not data.get("category"): return None

            return LanguageFeedback(**data)

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None

    def _mock_analysis(self, text: str) -> Optional[LanguageFeedback]:
        """A simple keyword-based mock for testing/demo purposes."""
        lower = text.lower()
        if "gonna" in lower:
            return LanguageFeedback(
                category=AnalysisCategory.SOCIOLINGUISTICS,
                suggestedCorrection=text.replace("gonna", "going to"),
                explanation="In formal contexts, 'going to' is preferred over 'gonna'.",
                detected_trigger="gonna"
            )
        if "she don't" in lower:
             return LanguageFeedback(
                category=AnalysisCategory.GRAMMAR,
                suggestedCorrection=text.replace("don't", "doesn't"),
                explanation="Third-person singular requires 'doesn't'.",
                detected_trigger="she don't"
            )
        return None
