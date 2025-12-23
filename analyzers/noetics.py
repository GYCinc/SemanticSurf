from enum import Enum

class SixNotableNoetics(str, Enum):
    """
    The Six Notable Noetics.

    These are the ONLY user-facing categories allowed in the UI and Reports.
    All granular linguistic phenomena must map to one of these six.
    """
    GRAMMAR = "Grammar"
    VOCABULARY = "Vocabulary"
    PHRASAL_VERBS = "Phrasal Verbs"
    COLLOCATIONS = "Collocations"
    IDIOMS_AND_PHRASES = "Idioms & Phrases"
    FLUENCY_AND_FLOW = "Fluency & Flow"
