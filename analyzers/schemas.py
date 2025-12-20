from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class OfficialCategory(str, Enum):
    VOCAB_GAP = "VOCAB_GAP"
    GRAMMAR_ERR = "GRAMMAR_ERR"
    RECAST = "RECAST"
    AVOIDANCE = "AVOIDANCE"
    PRONUNCIATION = "PRONUNCIATION"

class LinguisticSubcategory(str, Enum):
    PHONOLOGY = "Phonology"
    LEXIS = "Lexis"
    SYNTAX = "Syntax"
    PRAGMATICS = "Pragmatics"

class LanguageFeedback(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    category: OfficialCategory = Field(description="The Official Box (e.g., VOCAB_GAP, GRAMMAR_ERR).")
    subcategory: LinguisticSubcategory = Field(description="Internal linguistic pillar (Phonology, Lexis, Syntax, Pragmatics).")
    specific_phenomenon: str = Field(alias="specificPhenomenon", description="The Real Shit: Granular detail (e.g., 'Cleft Sentence', 'Verb Tense').")
    suggested_correction: str = Field(alias="suggestedCorrection")
    explanation: str = Field(description="Linguistic explanation.")
    detected_trigger: str = Field(alias="detectedTrigger")
    unstructured_insight: Optional[str] = Field(default=None, description="The TheGuru's Journal: High-fidelity nuances.")

class Turn(BaseModel):
    turn_order: int
    transcript: str
    speaker: str
    timestamp: str
    analysis: Optional[LanguageFeedback] = None