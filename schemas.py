from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# --- 1. The 8 Immutable Categories ---
class AnalysisCategory(str, Enum):
    PHRASAL_VERBS = "Phrasal Verbs"
    VOCABULARY = "Vocabulary"
    EXPRESSIONS = "Expressions"
    GRAMMAR = "Grammar"
    PRONUNCIATION = "Pronunciation"
    FLOW = "Flow"
    DISCOURSE = "Discourse"
    SOCIOLINGUISTICS = "Sociolinguistics"

# --- 2. Analysis Payload ---
class LanguageFeedback(BaseModel):
    category: AnalysisCategory = Field(..., description="The linguistic category of the issue.")
    suggested_correction: str = Field(..., description="The natural, corrected version of the sentence.", alias="suggestedCorrection")
    explanation: str = Field(..., description="A concise explanation of the error (max 2 sentences).")
    detected_trigger: Optional[str] = Field(None, description="The specific word or phrase that triggered this feedback.")

# --- 3. Turn Data ---
class Turn(BaseModel):
    turn_order: int
    transcript: str
    speaker: str
    timestamp: Optional[str] = None
    analysis: Optional[LanguageFeedback] = None

    class Config:
        populate_by_name = True
