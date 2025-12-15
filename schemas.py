from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# --- 1. The 4 Internal Linguistic Categories (SLA Domains) ---
# These are for analysis/classification, NOT student-facing
class AnalysisCategory(str, Enum):
    PHONOLOGY = "Phonology"       # Pronunciation, Intonation, Stress
    LEXIS = "Lexis"               # Vocabulary, Collocations, Formulaic Language
    SYNTAX = "Syntax"             # Grammar, Morphology, Sentence Structure
    PRAGMATICS = "Pragmatics"     # Discourse, Coherence, Register, Appropriateness


# --- 2. The 6 Student-Facing Categories (publicCategory) ---
# These are what students see in the UI - IMMUTABLE
class PublicCategory(str, Enum):
    GRAMMAR = "Grammar"
    VOCABULARY = "Vocabulary"
    PHRASAL_VERBS = "Phrasal Verbs"
    COLLOCATIONS = "Collocations"
    IDIOMS_PHRASES = "Idioms & Phrases"
    FLUENCY_FLOW = "Fluency & Flow"


# --- 3. Mapping: Internal 4 → Public 6 ---
# Default mapping - can be refined based on detected_trigger context
CATEGORY_MAPPING = {
    AnalysisCategory.PHONOLOGY: PublicCategory.FLUENCY_FLOW,
    AnalysisCategory.LEXIS: PublicCategory.VOCABULARY,  # Default, but could be Phrasal Verbs/Collocations/Idioms
    AnalysisCategory.SYNTAX: PublicCategory.GRAMMAR,
    AnalysisCategory.PRAGMATICS: PublicCategory.FLUENCY_FLOW,
}


def map_to_public_category(internal: AnalysisCategory, detected_trigger: Optional[str] = None) -> PublicCategory:
    """
    Maps internal SLA category to student-facing publicCategory.
    Uses detected_trigger to refine Lexis → specific subcategory.
    """
    if internal == AnalysisCategory.LEXIS and detected_trigger:
        trigger_lower = detected_trigger.lower()
        # Check for phrasal verb patterns (verb + particle)
        if any(particle in trigger_lower for particle in [' up', ' down', ' out', ' in', ' off', ' on', ' over', ' away']):
            return PublicCategory.PHRASAL_VERBS
        # Check for idiom/fixed phrase patterns
        if any(marker in trigger_lower for marker in ['the ', 'a ', 'in ', 'at ', 'by ']):
            return PublicCategory.IDIOMS_PHRASES
        # Check for collocation patterns (adj+noun, verb+noun common pairs)
        if ' ' in trigger_lower and len(trigger_lower.split()) == 2:
            return PublicCategory.COLLOCATIONS
    
    return CATEGORY_MAPPING.get(internal, PublicCategory.VOCABULARY)


# --- 4. Analysis Payload ---
class LanguageFeedback(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    category: AnalysisCategory = Field(..., description="The internal linguistic category of the issue.")
    suggested_correction: str = Field(..., description="The natural, corrected version of the sentence.", alias="suggestedCorrection")
    explanation: str = Field(..., description="A concise explanation of the error (max 2 sentences).")
    detected_trigger: Optional[str] = Field(None, description="The specific word or phrase that triggered this feedback.", alias="detectedTrigger")
    
    @property
    def public_category(self) -> PublicCategory:
        """Returns the student-facing category."""
        return map_to_public_category(self.category, self.detected_trigger)


# --- 5. Turn Data ---
class Turn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    turn_order: int
    transcript: str
    speaker: str
    timestamp: Optional[str] = None
    analysis: Optional[LanguageFeedback] = None
