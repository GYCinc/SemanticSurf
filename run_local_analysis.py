import sys
import os
import json
import logging
import uuid
import uuid
from datetime import datetime
from typing import Any, cast, Mapping, Sequence, Dict, List

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LocalAnalysis")

# Ensure imports work if run as script
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

from AssemblyAIv2.analyzers.session_analyzer import SessionAnalyzer
from AssemblyAIv2.analyzers.pos_analyzer import POSAnalyzer
from AssemblyAIv2.analyzers.ngram_analyzer import NgramAnalyzer
from AssemblyAIv2.analyzers.verb_analyzer import VerbAnalyzer
from AssemblyAIv2.analyzers.article_analyzer import ArticleAnalyzer
from AssemblyAIv2.analyzers.amalgum_analyzer import AmalgumAnalyzer
from AssemblyAIv2.analyzers.comparative_analyzer import ComparativeAnalyzer
from AssemblyAIv2.analyzers.phenomena_matcher import ErrorPhenomenonMatcher
from AssemblyAIv2.analyzers.preposition_analyzer import PrepositionAnalyzer
from AssemblyAIv2.analyzers.learner_error_analyzer import LearnerErrorAnalyzer
from AssemblyAIv2.analyzers.lexical_engine import LexicalEngine
from AssemblyAIv2.analyzers.fluency_analyzer import FluencyAnalyzer

def run_tiered_analysis(
    student_name: str, 
    all_turns: List[Dict[str, Any]], 
    notes: str = "Tutor notes",
    sentences: List[Any] | None = None,
    punctuated_text: str | None = None,
    raw_text: str | None = None
) -> Dict[str, Any]:
    """
    Runs the full deterministic analysis suite (POS, Ngrams, Verbs, etc.) locally.
    Accepts all 4 transcript components for completeness:
    1. Turns (Words)
    2. Sentences
    3. Punctuated Text (Diarized)
    4. Raw Text
    """
    logger.info(f"🧠 Running Tiered Analysis Suite for {student_name}...")

    # Construct unified JSON structure expected by SessionAnalyzer
    session_json = {
        "session_id": str(uuid.uuid4()),
        "student_name": student_name,
        "teacher_name": "Aaron",
        "speaker_map": {"A": "Aaron", "B": student_name}, # Heuristic, assuming normalized speakers
        "start_time": datetime.now().isoformat(),
        "turns": all_turns,
        "notes": notes,
        "sentences": sentences or [],
        "punctuated_transcript": punctuated_text or "",
        "raw_transcript": raw_text or ""
    }

    # 1. Main Session Analysis
    main_analyzer = SessionAnalyzer(cast(Dict[str, object], session_json))
    basic_metrics = main_analyzer.analyze_all()
    student_text = main_analyzer.student_full_text
    tutor_text = main_analyzer.teacher_full_text
    
    # 2. Sub-Analyzers (Optional Dependencies safe)
    pos_counts: Mapping[str, object] = {}
    pos_ratios: Mapping[str, object] = {}
    ngram_data: Mapping[str, object] = {}
    verb_data: Mapping[str, object] = {}
    article_data: Sequence[object] = []
    prep_data: Sequence[object] = []
    learner_data: Sequence[object] = []

    try:
        pos_counts = POSAnalyzer().analyze(student_text)
        pos_ratios = POSAnalyzer().get_ratios(student_text)
        ngram_data = NgramAnalyzer().analyze(student_text)
        verb_data = VerbAnalyzer().analyze(student_text)
        article_data = ArticleAnalyzer().analyze(student_text)
        prep_data = PrepositionAnalyzer().analyze(student_text)
        learner_data = LearnerErrorAnalyzer().analyze(student_text)
    except ModuleNotFoundError as e:
        logger.warning(f"⚠️ Optional NLP dependency missing; continuing without full tiered suite: {e}")
    except Exception as e:
        logger.error(f"⚠️ Error during NLP analysis sub-modules: {e}")

    # 3. Comparative Analysis
    comp_data: Dict[str, Any] = {}
    try:
        comp_data = cast(Dict[str, Any], ComparativeAnalyzer().compare(
            student_data={"pos": pos_counts, "ngrams": ngram_data, "text": student_text},
            tutor_data={
                "pos": POSAnalyzer().analyze(tutor_text),
                "ngrams": NgramAnalyzer().analyze(tutor_text),
                "text": tutor_text,
            },
        ))
    except ModuleNotFoundError as e:
        logger.warning(f"⚠️ Comparative analysis skipped: {e}")
    except Exception as e:
         logger.warning(f"⚠️ Comparative analysis failed: {e}")

    # 4. Error Consolidator
    detected_errors = []
    
    # Standardize Article Errors
    if isinstance(article_data, (list, tuple)):
        detected_errors.extend([{'error_type': 'Article Error', 'text': cast(Dict[str, object], e)['match']} for e in article_data])
    
    # Standardize Verb Errors
    verb_errs = cast(Dict[str, object], verb_data).get('irregular_errors', [])
    if isinstance(verb_errs, list):
        detected_errors.extend([{'error_type': 'Verb Error', 'text': cast(Dict[str, object], e)['verb']} for e in verb_errs])

    # Standardize Preposition Errors
    detected_errors.extend([{'error_type': 'Preposition Error', 'text': cast(Dict[str, object], e)['item']} for e in prep_data])

    # Standardize Learner Errors (PELIC)
    detected_errors.extend([{'error_type': f"Learner: {cast(Dict[str, object], e).get('category')}", 'text': cast(Dict[str, object], e)['item']} for e in learner_data])
    
    # Pattern Matching
    try:
        pattern_matches = ErrorPhenomenonMatcher().match(student_text)
        for m in pattern_matches:
            detected_errors.append({'error_type': f"Pattern: {m.get('category')}", 'text': m.get('item')})
    except: pass

    # 5. Final Context Construction
    fluency_analyzer = FluencyAnalyzer()
    student_words = [w for t in main_analyzer.student_turns_list for w in t.get('words', [])]

    analysis_context = {
        "caf_metrics": cast(Dict[str, Any], basic_metrics).get('student_metrics', {}).get('caf_metrics') or "DATA_MISSING",
        "student_metrics": cast(Dict[str, Any], basic_metrics).get('student_metrics', {}),
        "teacher_metrics": cast(Dict[str, Any], basic_metrics).get('teacher_metrics', {}),
        "comparison": comp_data,
        "register_analysis": {"scores": AmalgumAnalyzer().analyze_register(student_text), "classification": AmalgumAnalyzer().get_genre_classification(student_text)},
        "detected_errors": detected_errors,
        "pos_summary": pos_ratios,
        "lexical_analysis": LexicalEngine().analyze_production(student_words),
        "fluency_analysis": {
            "hesitation": fluency_analyzer.analyze_hesitation(student_words),
            "articulation_rate": fluency_analyzer.calculate_articulation_rate(student_words)
        }
    }
    
    logger.info("✅ Tiered Analysis Complete")
    return analysis_context

if __name__ == "__main__":
    print("Run this module via import or provide a test JSON file path to analyze.")
