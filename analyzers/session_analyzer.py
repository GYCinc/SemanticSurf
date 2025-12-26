#!/usr/bin/env python3
# pyright: reportMissingImports=false
# pyright: reportMissingTypeStubs=false
# pyright: reportAny=false
# pyright: reportExplicitAny=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnreachable=false
# pyright: reportUnusedParameter=false
from __future__ import annotations
"""
Comprehensive Session Analysis Engine (STUDENT-ONLY + LOCAL AI)
Analyzes ESL lesson transcripts for teaching insights using local, free tools.
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import cast, Any, Callable, final
from collections.abc import Mapping, Iterable
import sys
import logging
from AssemblyAIv2.analyzers.lexical_engine import LexicalEngine
from AssemblyAIv2.analyzers.learner_error_analyzer import LearnerErrorAnalyzer

try:
    from textblob import TextBlob # type: ignore
    textblob_available = True
except ImportError:
    print("WARNING: textblob not found. Run 'pip install textblob' for advanced metrics.")
    textblob_available = False
    TextBlob = None  # type: ignore

# NLTK for advanced NLP (Penn Treebank POS, WordNet, N-grams)
try:
    import nltk # type: ignore
    from nltk.tokenize import word_tokenize, sent_tokenize # type: ignore
    from nltk.util import ngrams # type: ignore
    from nltk import pos_tag # type: ignore
    
    nltk_available = True
    # Ensure required data is downloaded
    for resource in ['punkt', 'averaged_perceptron_tagger', 'wordnet', 'punkt_tab', 'averaged_perceptron_tagger_eng']:
        try:
            # Safely check data via casted find
            find_func: Callable[[str], object] = cast(Any, nltk.data).find
            _ = find_func(f'tokenizers/{resource}' if 'punkt' in resource else f'taggers/{resource}' if 'tagger' in resource else f'corpora/{resource}')
        except LookupError:
            try:
                download_func: Callable[[str], bool] = cast(Any, nltk).download
                _ = download_func(resource)
            except:
                pass
except ImportError:
    nltk_available = False
    print("WARNING: nltk not found. Run 'pip install nltk' for POS tagging and n-grams.")
    word_tokenize = None
    sent_tokenize = None
    ngrams = None
    pos_tag = None

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@final
class SessionAnalyzer:
    """Analyzes session data for ESL teaching insights"""
    session: Mapping[str, Any]
    turns: list[dict[str, object]]
    speaker_map: dict[str, object]
    teacher_name: str
    student_name: str
    student_label: str
    teacher_label: str
    student_turns_list: list[dict[str, Any]]
    student_full_text: str
    teacher_turns: list[dict[str, dict[str, Any]]]
    teacher_full_text: str

    def __init__(self, session_data: Mapping[str, Any]):
        self.session = session_data
        # Support both 'turns' and 'speaker_segments'
        self.turns = cast(list[dict[str, object]], session_data.get('turns', []))
        if not self.turns:
            self.turns = cast(list[dict[str, object]], session_data.get('speaker_segments', []))

        # --- Find the Student AND Teacher ---
        self.speaker_map = cast(dict[str, object], session_data.get('speaker_map', {}))
        self.teacher_name = cast(str, session_data.get('teacher_name', 'Teacher'))
        self.student_name = cast(str, session_data.get('student_name', 'Student'))

        self.student_label = 'Unknown'
        self.teacher_label = 'Unknown'
        
        # If speaker_map is missing, try to infer it from turns or direct usage
        if not self.speaker_map:
            # Check if speakers are identified directly in turns
            speakers = set()
            for t in self.turns:
                spk = t.get('speaker')
                if spk:
                    speakers.add(str(spk))
            
            # Simple inference: map speaker label to themselves if they match names
            for s in speakers:
                self.speaker_map[s] = s

        for label, name in self.speaker_map.items():
            if name == self.student_name:
                self.student_label = label
            elif name == self.teacher_name:
                self.teacher_label = label
        
        # Fallback: Check for "Student"/"Teacher" literals if specific names didn't match
        if self.student_label == 'Unknown':
            for label, name in self.speaker_map.items():
                if "Student" in name or "Student" in label:
                    self.student_label = label
                    break
        
        if self.teacher_label == 'Unknown':
            for label, name in self.speaker_map.items():
                if "Teacher" in name or "Teacher" in label:
                    self.teacher_label = label
                    break

        # Student setup
        if self.student_label == 'Unknown':
            logger.warning("Could not find student label in speaker_map. Analysis may be empty.")
            self.student_turns = []
            self.student_turns_list = []  # Fix AttributeError
            self.student_full_text = ""
        else:
            logger.info(f"Analyzer: Found Student '{self.student_name}' with label '{self.student_label}'")
            self.student_turns_list = cast(list[dict[str, Any]], self._get_turns_for_speaker(self.student_label))
            self.student_full_text = " ".join([cast(str, t.get('transcript', t.get('text', ''))) for t in self.student_turns_list])

        # Teacher setup
        if self.teacher_label == 'Unknown':
            logger.warning("Could not find teacher label in speaker_map.")
            self.teacher_turns = []
            self.teacher_full_text = ""
        else:
            logger.info(f"Analyzer: Found Teacher '{self.teacher_name}' with label '{self.teacher_label}'")
            self.teacher_turns = cast(list[dict[str, Any]], self._get_turns_for_speaker(self.teacher_label))
            self.teacher_full_text = " ".join([cast(str, t.get('transcript', t.get('text', ''))) for t in self.teacher_turns])

        # Initialize LexicalEngine for high-fidelity vocab analysis
        self.lexical_engine = LexicalEngine()

        # Capture Raw/Punctuated for Corpus Logic
        self.raw_text = str(session_data.get('raw_transcript', ''))
        self.punctuated_text = str(session_data.get('punctuated_transcript', ''))

        # --- Enriched Metadata (Auto-Calculate if missing) ---
        self._enrich_metadata()

    def _enrich_metadata(self):
        """
        Robustly populate missing metadata (timestamps, pauses, WPM) 
        derived from raw word-level data.
        """
        for turn in self.turns:
            words = cast(list[dict[str, Any]], turn.get('words', []))
            if not words: continue

            # 1. Infer Turn Timestamps (if missing)
            start_key = 'start' if 'start' in turn else 'start_ms'
            end_key = 'end' if 'end' in turn else 'end_ms'
            
            if turn.get(start_key) is None and words:
                # Handle both 'start' and 'start_ms' in words
                w_start = words[0].get('start') or words[0].get('start_ms')
                if w_start is not None:
                    turn[start_key] = w_start
            
            if turn.get(end_key) is None and words:
                w_end = words[-1].get('end') or words[-1].get('end_ms')
                if w_end is not None:
                    turn[end_key] = w_end

            # 2. Ensure Analysis Dict Exists
            if 'analysis' not in turn:
                turn['analysis'] = {}
            analysis = cast(dict[str, Any], turn['analysis'])

            # 3. Calculate Pauses (if missing)
            if 'pauses' not in analysis:
                pauses = []
                for i in range(len(words) - 1):
                    w_curr = words[i]
                    w_next = words[i+1]
                    
                    curr_end = w_curr.get('end') or w_curr.get('end_ms') or 0
                    next_start = w_next.get('start') or w_next.get('start_ms') or 0
                    
                    gap = float(next_start) - float(curr_end)
                    if gap > 300: # 300ms threshold for pause
                        pauses.append({
                            'start_ms': curr_end,
                            'end_ms': next_start,
                            'duration_ms': gap
                        })
                analysis['pauses'] = pauses

            # 4. Calculate WPM (if missing)
            if 'speaking_rate_wpm' not in analysis:
                t_start = turn.get(start_key)
                t_end = turn.get(end_key)
                if t_start is not None and t_end is not None:
                    duration_min = (float(t_end) - float(t_start)) / 1000.0 / 60.0
                    if duration_min > 0.001:
                        analysis['speaking_rate_wpm'] = len(words) / duration_min
                    else:
                        analysis['speaking_rate_wpm'] = 0.0


    def _analyze_learner_errors(self, text: str) -> list[dict[str, Any]]:
        """Run the robust LearnerErrorAnalyzer"""
        try:
            analyzer = LearnerErrorAnalyzer()
            return analyzer.analyze(text)
        except Exception as e:
            logger.error(f"LearnerErrorAnalyzer failed: {e}")
            return []

    def analyze_all(self) -> dict[str, Any]:
        """Run all analyses for BOTH student and teacher with comparisons"""

        student_metrics = {
            'speaking_rate': self.analyze_speaking_rate(self.student_turns_list),
            'pauses': self.analyze_pauses(self.student_turns_list),
            'complexity_basic': self.analyze_complexity(self.student_turns_list),
            'vocabulary_analysis': self.analyze_vocabulary(),
            'advanced_local_analysis': self.run_textblob_analysis(),
            'fillers': self.analyze_fillers(self.student_turns_list),
            'hesitation_patterns': self.analyze_hesitation_patterns(self.student_turns_list),
        # SLA Framework additions
            'ngram_analysis': self.analyze_ngrams(self.student_full_text),
            'pos_analysis': self.analyze_pos_tags(self.student_full_text),
            'caf_metrics': self.analyze_caf(self.student_turns_list),
            'learner_errors': self._analyze_learner_errors(self.student_full_text),  # [NEW] Robust Error Analysis
        }

        # --- Unified Phenomena Injection (The "Holy Mirror") ---
        # We augment the learner_errors with the dedicated Unified Phenomena Matcher
        try:
            from AssemblyAIv2.analyzers.phenomena_matcher import ErrorPhenomenonMatcher
            # Initialize (async init technically required for remote, but we use local mostly)
            # For this synchronous path, we rely on the matcher's __init__ or run a quick loop if needed.
            # However, PhenomenaMatcher.initialize is async.
            # We will instantiate and try to use what's available or run it synchronously if possible.
            # Looking at PhenomenaMatcher, it has an async initialize.
            # We'll use a helper to run it or rely on a synchronous fallback if strictly local?
            # Actually, let's just create it. The local patterns load in initialize().
            
            # Helper to run async init in sync context if needed, or just standard loop
            import asyncio
            matcher = ErrorPhenomenonMatcher()
            # We strictly need the local patterns loaded.
            loop = asyncio.new_event_loop()
            loop.run_until_complete(matcher.initialize())
            loop.close()
            
            unified_matches = matcher.match(self.student_full_text)
            
            # Merge into learner_errors
            # learner_errors is a list[dict]. We simply extend it.
            if isinstance(student_metrics['learner_errors'], list):
                student_metrics['learner_errors'].extend(unified_matches)
                logger.info(f"SessionAnalyzer: Injected {len(unified_matches)} unified phenomena matches.")
            else:
                 logger.warning("SessionAnalyzer: learner_errors is not a list, cannot inject unified matches.")
            
        except Exception as e:
            logger.warning(f"Unified Phenomena Matcher failed to run: {e}")

        teacher_metrics = {
            'speaking_rate': self.analyze_speaking_rate(self.teacher_turns),
            'pauses': self.analyze_pauses(self.teacher_turns),
            'complexity_basic': self.analyze_complexity(self.teacher_turns),
            'fillers': self.analyze_fillers(self.teacher_turns),
        }

        # --- COMPARATIVE ANALYSIS (The good stuff) ---
        # 1. Basic Stats Comparison
        basic_comparison = self._build_comparison(cast(dict[str, object], student_metrics), cast(dict[str, object], teacher_metrics))
        
        # 2. Deep Linguistic Comparison (ComparativeAnalyzer)
        deep_comparison = {}
        try:
            from AssemblyAIv2.analyzers.comparative_analyzer import ComparativeAnalyzer
            comp_analyzer = ComparativeAnalyzer()
            # We need student and teacher text.
            # Warning: self.teacher_full_text might be empty if no teacher turns found
            deep_comparison = comp_analyzer.analyze(self.teacher_full_text, self.student_full_text)
        except Exception as e:
            logger.warning(f"ComparativeAnalyzer failed: {e}")

        # Merge them (Deep overrides Basic where keys match, or keeps both)
        # We'll put basic into a key called 'stats' and deep into 'linguistics'
        final_comparison = {
            'stats': basic_comparison,
            'linguistics': deep_comparison.get('comparison', {}), 
            'tutor_linguistics': deep_comparison.get('tutor', {}),
            'student_linguistics': deep_comparison.get('student', {})
        }

        return {
            'session_info': self._get_session_info(),
            'student_metrics': student_metrics,
            'teacher_metrics': teacher_metrics,
            'comparison': final_comparison,
            'teacher_feedback': self._generate_teacher_feedback(basic_comparison),
            'marked_turns': self._get_marked_turns_summary(),
            'action_items': self._get_action_items(),
            'corpus_review': self._generate_corpus_review() # [NEW] Human-in-the-Loop Corpus Injection
            # 'lm_analysis' added by lm_gateway.py
        }

    def _generate_corpus_review(self) -> dict[str, Any]:
        """
        Generates the 'Corpus Injection' review package.
        See: ASSEMBLYAI BIBLE - Dual-Pass Protocol
        Use Diarized/Punctuated text as the 'Source of Truth' for student credits.
        """
        import uuid
        import os
        
        # 1. Extract Student Lemmas (using LexicalEngine)
        # Result is a Dict with keys: 'words', 'raw_text', 'unknown_ratio', etc.
        lex_result = self.lexical_engine.analyze_production([w for t in self.student_turns_list for w in t.get('words', [])])
        
        # We need a clean LIST of proposed lemmas/words, not the whole dict.
        # Filter for:
        # - Whitelisted (Real words)
        # - Not 'unknown'
        # - Unique entries
        # FIXED: Use 'resolved_word' (Exact dictionary match) instead of 'lemma' (Stem)
        # This ensures 'talking' and 'talk' are distinct if both are in the dictionary.
        unique_lemmas = sorted(list(set(
            w['resolved_word'] for w in lex_result.get('words', []) 
            if w.get('is_whitelisted') and w.get('resolved_word')
        )))

        review_packet = {
            "session_id": self.session.get('session_id', str(uuid.uuid4())),
            "student_name": self.student_name,
            "timestamp": "Now",
            "injection_status": "PENDING_REVIEW",
            "validation_source": "DIARIZED_TRANSCRIPT",
            "validation_method": "Exact Dictionary Match + Fuzzy (Cognitive Effort Credit)",
            "raw_check": "Available in .session_captures",
            "proposed_corpus_additions": unique_lemmas, # List of resolved words
             # Snippets for quick context
            "transcript_snippet": self.student_full_text[:500] + "..." if len(self.student_full_text) > 500 else self.student_full_text
        }
        
        # 2. Write to Admin Inbox
        inbox_dir = Path(self.session.get('workspace_root', '.')) / "AssemblyAIv2/admin_inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"corpus_review_{self.student_name}_{uuid.uuid4().hex[:8]}.json"
        
        try:
            with open(inbox_dir / filename, 'w') as f:
                json.dump(review_packet, f, indent=2)
            logger.info(f"📨 Corpus Review Packet sent to: {inbox_dir / filename}")
        except Exception as e:
            logger.error(f"Failed to write Corpus Review: {e}")
            
        return review_packet

    def _get_session_info(self) -> dict[str, object]:
        """Basic session information"""
        return {
            'speaker_map': self.speaker_map
        }

    def _get_turns_for_speaker(self, speaker_label: str) -> list[dict[str, object]]:
        """Helper to filter turns for a specific speaker label"""
        if speaker_label == 'Unknown': return []
        return [t for t in self.turns if t.get('speaker') == speaker_label]

    # --- NEW: Free, Local, "Smart" Analysis ---
    def run_textblob_analysis(self) -> dict[str, object]:
        """
        Runs TextBlob analysis on the student's full text.
        This is the "free" open-source analysis you wanted.
        """
        if not textblob_available or not self.student_full_text or TextBlob is None: # type: ignore
            return {'error': 'TextBlob not available or no student text.'}

        try:
            if not textblob_available:
                return {'error': 'TextBlob not available.'}
            blob = TextBlob(self.student_full_text)

            # 1. Polarity: How positive/negative (range -1.0 to 1.0)
            sentiment = getattr(blob, 'sentiment', None)
            polarity = 0.0
            subjectivity = 0.0
            if sentiment:
                polarity = round(float(getattr(cast(object, sentiment), 'polarity', 0.0)), 2)
                subjectivity = round(float(getattr(cast(object, sentiment), 'subjectivity', 0.0)), 2)

            # 3. Noun Phrases: Find key topics
            # We find the top 5 most frequent topics they discussed
            all_noun_phrases = cast(list[object], getattr(blob, 'noun_phrases', []))
            noun_phrases = [str(p) for p in all_noun_phrases if len(str(p)) > 1]
            top_noun_phrases = dict(Counter(noun_phrases).most_common(5))

            return {
                'sentiment_polarity': polarity,
                'sentiment_subjectivity': subjectivity,
                'top_noun_phrases': top_noun_phrases,
                'polarity_assessment': self._assess_polarity(polarity),
                'subjectivity_assessment': self._assess_subjectivity(subjectivity)
            }
        except Exception as e:
            logger.error(f"TextBlob analysis failed: {e}")
            return {'error': str(e)}

    def _assess_polarity(self, score: float) -> str:
        if score > 0.3: return "Very Positive"
        if score > 0.1: return "Positive"
        if score < -0.3: return "Very Negative"
        if score < -0.1: return "Negative"
        return "Neutral"

    def _assess_subjectivity(self, score: float) -> str:
        if score > 0.7: return "Very Opinionated"
        if score > 0.4: return "Opinionated"
        return "Objective"
    # --- END NEW ---

    def analyze_speaking_rate(self, turns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Analyze words per minute over time"""
        if turns is None:
            turns = self.student_turns_list
        rates: list[dict[str, int | float]] = []
        for turn in turns:
            # Now safely relies on enriched metadata
            analysis = cast(dict[str, object], turn.get('analysis', {}))
            wpm = analysis.get('speaking_rate_wpm')
            
            if wpm is not None and float(wpm) > 0:
                rates.append({'turn_order': cast(int, turn.get('turn_order', 0)), 'wpm': float(wpm)})

        if not rates: return {'error': 'No speaking rate data', 'average_wpm': 0.0}

        wpms = [float(r['wpm']) for r in rates]
        avg_wpm = sum(wpms) / len(wpms)
        return {
            'average_wpm': round(avg_wpm, 1),
            'min_wpm': round(min(wpms), 1),
            'max_wpm': round(max(wpms), 1),
            'turn_count': len(turns)
        }

        wpms = [float(r['wpm']) for r in rates]
        avg_wpm = sum(wpms) / len(wpms)
        return {
            'average_wpm': round(avg_wpm, 1),
            'min_wpm': round(min(wpms), 1),
            'max_wpm': round(max(wpms), 1),
            'turn_count': len(turns)
        }

    def analyze_pauses(self, turns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Analyze pause patterns"""
        if turns is None:
            turns = self.student_turns_list
        all_pauses: list[float] = []
        long_pauses: list[float] = []
        for turn in turns:
            analysis = cast(dict[str, object], turn.get('analysis', {})).get('pauses', [])
            for pause in cast(list[dict[str, object]], analysis):
                duration = float(cast(float, pause.get('duration_ms', 0.0)))
                all_pauses.append(duration)
                if duration > 1000:
                    long_pauses.append(duration)

        if not all_pauses: return {'message': 'No pause data'}

        return {
            'total_pauses': len(all_pauses),
            'long_pauses_gt_1s': len(long_pauses),
            'average_pause_ms': round(sum(all_pauses) / len(all_pauses), 1),
            'total_pause_time_ms': sum(all_pauses)
        }

    def analyze_complexity(self, turns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Analyze vocabulary complexity"""
        if turns is None:
            turns = self.student_turns_list
        all_words: list[str] = []
        for turn in turns:
            words = cast(list[dict[str, object]], turn.get('words', []))
            all_words.extend([str(w.get('text', '')).lower() for w in words])

        if not all_words:
            return {'error': 'No word data', 'total_words': 0}

        unique_words = set(all_words)
        total_unique = len(unique_words)
        total_all = len(all_words)
        return {
            'total_words': total_all,
            'unique_words': total_unique,
            'vocabulary_diversity': round(total_unique / total_all, 3) if total_all > 0 else 0,
        }

    def analyze_fillers(self, turns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Count filler words"""
        if turns is None:
            turns = self.student_turns_list
        fillers = ['um', 'uh', 'like', 'you know', 'so', 'well', 'actually']
        filler_counts: Counter[str] = Counter()
        total_words = 0
        for turn in turns:
            text = cast(str, turn.get('transcript', '')).lower()
            words = cast(list[object], turn.get('words', []))
            total_words += len(words)
            for filler in fillers:
                count = len(re.findall(r'\b' + filler + r'\b', text))
                if count > 0:
                    filler_counts[filler] += count

        total_fillers = sum(filler_counts.values())

        return {
            'total_fillers': total_fillers,
            'filler_percentage': round(total_fillers / total_words * 100, 2) if total_words > 0 else 0,
            'by_type': dict(filler_counts.most_common(5)),
        }

    def analyze_hesitation_patterns(self, turns: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Find words that precede long pauses - potential avoidance patterns"""
        if turns is None:
            turns = self.student_turns_list
        
        hesitation_words: list[dict[str, str | float]] = []  # Words before long pauses
        
        for turn in turns:
            words = cast(list[dict[str, object]], turn.get('words', []))
            pauses = cast(list[dict[str, object]], cast(dict[str, object], turn.get('analysis', {})).get('pauses', []))
            
            if not words or not pauses:
                continue
            
            # Create a map of word end times
            for pause in pauses:
                duration = cast(float, pause.get('duration_ms', 0))
                if duration > 800:  # Long pause threshold
                    pause_start = float(cast(float, pause.get('start_ms', 0)))
                    
                    # Find word that ended just before this pause
                    for word in words:
                        word_end = float(cast(float, word.get('end_ms', word.get('end', 0))))
                        # If word ended within 200ms of pause start, it's the hesitation point
                        if abs(word_end - pause_start) < 200:
                            hesitation_words.append({
                                'word': str(word.get('text', '')),
                                'pause_duration_ms': float(duration),
                                'confidence': float(cast(float, word.get('confidence', 1.0)))
                            })
                            break
        
        # Count frequency of hesitation words
        word_freq: Counter[str] = Counter([str(w['word']).lower() for w in hesitation_words])
        
        return {
            'total_hesitations': len(hesitation_words),
            'frequent_hesitation_words': dict(word_freq.most_common(10)),
            'details': hesitation_words[:20]  # First 20 for inspection
        }

    # =========================================================================
    # SLA FRAMEWORK ANALYSIS (N-grams, POS, CAF)
    # Per: LEXICAL RESOURCES/SLA Transcript Analysis Framework.txt
    # =========================================================================

    def _get_wordnet_pos(self, treebank_tag: str) -> str:
        """Convert Penn Treebank POS tag to WordNet POS tag for lemmatization"""
        # This method is no longer strictly needed for lemmatization with LexicalEngine,
        # but kept for potential future NLTK WordNet usage if desired.
        if not nltk_available:
            return 'n'
        # Placeholder for wordnet if it were still imported
        # from nltk.corpus import wordnet
        # if treebank_tag.startswith('J'):
        #     return wordnet.ADJ
        # elif treebank_tag.startswith('V'):
        #     return wordnet.VERB
        # elif treebank_tag.startswith('N'):
        #     return wordnet.NOUN
        # elif treebank_tag.startswith('R'):
        #     return wordnet.ADV
        # else:
        return 'n'  # Default to noun

    def analyze_ngrams(self, text: str, n_range: tuple[int, int] = (2, 4)) -> dict[str, object]:
        """
        Extract n-grams (bigrams, trigrams, 4-grams) for formulaic language detection.
        AntConc-style cluster/n-gram analysis per SLA Framework.
        """
        if not nltk_available or not text:
            return {'error': 'NLTK not available or no text', 'bigrams': [], 'trigrams': [], 'fourgrams': []}
        
        try:
            # Tokenize and clean
            tokens = word_tokenize(text.lower()) if word_tokenize is not None else []
            # Filter out punctuation and short tokens
            tokens = [t for t in tokens if t.isalpha() and len(t) > 1]
            
            results = {}
            for n in range(n_range[0], n_range[1] + 1):
                if ngrams is not None:
                    grams_raw = ngrams(tokens, n)
                    n_grams = list(grams_raw) if grams_raw else []
                    # Count frequencies
                    ngram_freq: Counter[str] = Counter([' '.join(cast(Iterable[str], gram)) for gram in n_grams])
                    # Get top 15 most common
                    top_ngrams = ngram_freq.most_common(15)
                    
                    label = {2: 'bigrams', 3: 'trigrams', 4: 'fourgrams'}.get(n, f'{n}grams')
                    results[label] = [{'phrase': str(phrase), 'count': int(count)} for phrase, count in top_ngrams]
            
            # Identify formulaic sequences (repeated 3+ times)
            formulaic: list[dict[str, str | int]] = []
            for n in range(2, 5):
                if ngrams is not None:
                    n_grams = list(ngrams(tokens, n))
                    ngram_freq = Counter([' '.join(cast(Iterable[str], gram)) for gram in n_grams])
                    for phrase, count in ngram_freq.items():
                        if count >= 3:
                            formulaic.append({'phrase': phrase, 'count': int(count), 'length': n})
            
            results['formulaic_sequences'] = sorted(formulaic, key=lambda x: int(x.get('count', 0)), reverse=True)[:10]
            
            return cast(dict[str, object], results)
            
        except Exception as e:
            logger.error(f"N-gram analysis failed: {e}")
            return {'error': str(e)}

    def analyze_pos_tags(self, text: str) -> dict[str, object]:
        """
        Penn Treebank POS tagging with WordNet lemmatization.
        Returns POS distribution and vocabulary by category.
        """
        if not nltk_available or word_tokenize is None or pos_tag is None or not text:
            return {'error': 'NLTK not available or no text'}
            
        try:
            tokens = word_tokenize(text) if word_tokenize is not None else []
            tagged = pos_tag(tokens) if pos_tag is not None else []
            
            # Categorize by Penn Treebank tags
            pos_categories: dict[str, list[str]] = {
                'nouns': [],      # NN, NNS, NNP, NNPS
                'verbs': [],      # VB, VBD, VBG, VBN, VBP, VBZ
                'adjectives': [], # JJ, JJR, JJS
                'adverbs': [],    # RB, RBR, RBS
                'prepositions': [], # IN
                'determiners': [], # DT
                'pronouns': [],   # PRP, PRP$, WP
                'other': []
            }
            
            lemmas: list[str] = []
            pos_counts: Counter[str] = Counter()
            
            for word, tag in tagged:
                if not word.isalpha():
                    continue
                    
                pos_counts[tag] += 1
                
                # Lemmatize with High-Fidelity LexicalEngine (Deterministic Suffix Stripping)
                lemma = self.lexical_engine.lemmatize(word.lower())
                lemmas.append(lemma)
                
                # Categorize
                if tag.startswith('NN'):
                    pos_categories['nouns'].append(lemma)
                elif tag.startswith('VB'):
                    pos_categories['verbs'].append(lemma)
                elif tag.startswith('JJ'):
                    pos_categories['adjectives'].append(lemma)
                elif tag.startswith('RB'):
                    pos_categories['adverbs'].append(lemma)
                elif tag == 'IN':
                    pos_categories['prepositions'].append(word.lower())
                elif tag == 'DT':
                    pos_categories['determiners'].append(word.lower())
                elif tag.startswith('PRP') or tag.startswith('WP'):
                    pos_categories['pronouns'].append(word.lower())
                else:
                    pos_categories['other'].append(word.lower())
            
            # Get unique items per category
            unique_by_category: dict[str, list[str]] = {k: sorted(list(set(v))) for k, v in pos_categories.items()}
            counts_by_category = {k: len(v) for k, v in pos_categories.items()}
            
            # Content word ratio (nouns + verbs + adjectives + adverbs / total)
            content_words = len(pos_categories['nouns']) + len(pos_categories['verbs']) + \
                           len(pos_categories['adjectives']) + len(pos_categories['adverbs'])
            total_words = sum(counts_by_category.values())
            lexical_density = round(content_words / total_words, 3) if total_words > 0 else 0
            
            return {
                'pos_distribution': dict(pos_counts.most_common()),
                'counts_by_category': counts_by_category,
                'unique_by_category': {k: v[:20] for k, v in unique_by_category.items()},  # Top 20 each
                'total_unique_lemmas': len(set(lemmas)),
                'lexical_density': lexical_density,
                'content_word_ratio': f"{content_words}/{total_words}"
            }
            
        except Exception as e:
            logger.error(f"POS analysis failed: {e}")
            return {'error': str(e)}

    def analyze_caf(self, turns: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Complexity, Accuracy, Fluency (CAF) metrics.
        Per SLA Framework: MLT, C/T, Error-Free T-units, articulation rate.
        """
        if not turns:
            return {'error': 'No turns to analyze'}
        
        try:
            # Collect all text
            all_text = ' '.join([cast(str, t.get('transcript', '')) for t in turns])
            if not all_text:
                return {'error': 'No transcript text'}
            
            # T-unit approximation: Split by sentence boundaries
            # A T-unit = main clause + attached subordinate clauses
            # Approximation: sentences (split by . ! ?)
            sentences = re.split(r'[.!?]+', all_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            t_units = len(sentences)
            
            if t_units == 0:
                return {'error': 'No T-units detected'}
            
            # --- COMPLEXITY ---
            total_words = len(all_text.split())
            mlt = round(total_words / t_units, 2) if t_units > 0 else 0  # Mean Length of T-unit
            
            # Count clauses (approximation: count subordinating conjunctions + sentences)
            subordinators = ['that', 'which', 'who', 'whom', 'whose', 'when', 'where', 'while', 
                           'because', 'although', 'if', 'unless', 'since', 'after', 'before']
            clause_markers = sum(all_text.lower().count(f' {sub} ') for sub in subordinators)
            total_clauses = t_units + clause_markers
            c_t = round(total_clauses / t_units, 2) if t_units > 0 else 0  # Clauses per T-unit
            
            # --- FLUENCY ---
            # From existing pause/filler analysis
            total_pauses = sum(len(cast(list[object], cast(dict[str, object], t.get('analysis', {})).get('pauses', []))) for t in turns)
            total_fillers = 0
            filler_words = ['um', 'uh', 'like', 'you know', 'so', 'well', 'actually']
            for turn in turns:
                text = cast(str, turn.get('transcript', '')).lower()
                for filler in filler_words:
                    total_fillers += len(re.findall(r'\b' + filler + r'\b', text))
            
            # Mean Length of Run (words between pauses)
            mlr = round(total_words / (total_pauses + 1), 2) if total_pauses >= 0 else total_words
            
            # Filled pauses per 100 words
            filled_pause_rate = round((float(total_fillers) / float(total_words)) * 100, 2) if total_words > 0 else 0
            
            # --- ACCURACY (approximation) ---
            # We can't do true error detection without gold standard, but we can flag:
            # - Repeated words (false starts)
            # - Very short sentences (fragments)
            
            false_starts = len(re.findall(r'\b(\w+)\s+\1\b', all_text, re.IGNORECASE))
            short_tunits = sum(1 for s in sentences if len(s.split()) < 3)
            error_free_approx = t_units - short_tunits - false_starts
            error_free_pct = round((error_free_approx / t_units) * 100, 1) if t_units > 0 else 0
            
            return {
                'complexity': {
                    'total_t_units': t_units,
                    'total_words': total_words,
                    'mean_length_t_unit': mlt,
                    'clauses_per_t_unit': c_t,
                    'interpretation': 'Higher MLT and C/T = more complex syntax'
                },
                'fluency': {
                    'mean_length_run': mlr,
                    'total_pauses': total_pauses,
                    'filled_pause_rate_per_100': filled_pause_rate,
                    'interpretation': 'Higher MLR = more fluent; Lower pause rate = smoother'
                },
                'accuracy_approximation': {
                    'error_free_t_units_pct': max(0, error_free_pct),
                    'false_starts_detected': false_starts,
                    'fragments_detected': short_tunits,
                    'note': 'True accuracy requires human annotation'
                }
            }
            
        except Exception as e:
            logger.error(f"CAF analysis failed: {e}")
            return {'error': str(e)}

    def _build_comparison(self, student_metrics: Mapping[str, Any], teacher_metrics: Mapping[str, Any]) -> dict[str, Any]:
        """Build side-by-side comparison metrics"""
        student_complexity = cast(dict[str, object], student_metrics.get('complexity_basic', {}))
        teacher_complexity = cast(dict[str, object], teacher_metrics.get('complexity_basic', {}))
        
        student_words = cast(int, student_complexity.get('total_words', 0))
        teacher_words = cast(int, teacher_complexity.get('total_words', 0))
        total_words = student_words + teacher_words
        
        student_unique = cast(int, student_complexity.get('unique_words', 0))
        teacher_unique = cast(int, teacher_complexity.get('unique_words', 0))
        
        student_speaking = cast(dict[str, object], student_metrics.get('speaking_rate', {}))
        teacher_speaking = cast(dict[str, object], teacher_metrics.get('speaking_rate', {}))
        
        student_wpm = cast(float, student_speaking.get('average_wpm', 0))
        teacher_wpm = cast(float, teacher_speaking.get('average_wpm', 0))
        
        student_pauses_metrics = cast(dict[str, object], student_metrics.get('pauses', {}))
        teacher_pauses_metrics = cast(dict[str, object], teacher_metrics.get('pauses', {}))
        
        student_pauses = cast(int, student_pauses_metrics.get('total_pauses', 0))
        teacher_pauses = cast(int, teacher_pauses_metrics.get('total_pauses', 0))
        
        student_turns = cast(int, student_speaking.get('turn_count', 0))
        teacher_turns = cast(int, teacher_speaking.get('turn_count', 0))
        
        return {
            'talk_time_ratio': {
                'student_words': student_words,
                'teacher_words': teacher_words,
                'student_percentage': round(student_words / total_words * 100, 1) if total_words > 0 else 0,
                'teacher_percentage': round(teacher_words / total_words * 100, 1) if total_words > 0 else 0,
            },
            'vocabulary_calibration': {
                'student_unique_words': student_unique,
                'teacher_unique_words': teacher_unique,
                'teacher_to_student_ratio': round(teacher_unique / student_unique, 2) if student_unique > 0 else 0,
            },
            'speaking_rate_comparison': {
                'student_avg_wpm': student_wpm,
                'teacher_avg_wpm': teacher_wpm,
                'difference': round(teacher_wpm - student_wpm, 1),
            },
            'pause_comparison': {
                'student_pauses': student_pauses,
                'teacher_pauses': teacher_pauses,
            },
            'turn_balance': {
                'student_turns': student_turns,
                'teacher_turns': teacher_turns,
                'student_percentage': round(student_turns / (student_turns + teacher_turns) * 100, 1) if (student_turns + teacher_turns) > 0 else 0,
            }
        }

    def _generate_teacher_feedback(self, comparison: dict[str, object]) -> dict[str, object]:
        """Generate actionable feedback for the teacher based on comparison"""
        feedback: list[dict[str, str]] = []
        
        # Talk time analysis
        talk_ratio = cast(dict[str, object], comparison.get('talk_time_ratio', {}))
        student_pct = cast(float, talk_ratio.get('student_percentage', 0))
        if student_pct < 30:
            feedback.append({
                'type': 'warning',
                'area': 'Talk Time',
                'message': f'Student only spoke {student_pct}% of the session. Consider giving more space.'
            })
        elif student_pct >= 40 and student_pct <= 60:
            feedback.append({
                'type': 'positive',
                'area': 'Talk Time',
                'message': f'Excellent balance! Student spoke {student_pct}% of the session - ideal range.'
            })
        elif student_pct > 60:
            feedback.append({
                'type': 'positive',
                'area': 'Talk Time',
                'message': f'Great job letting the student lead! They spoke {student_pct}% of the session.'
            })
        elif student_pct >= 30:
            feedback.append({
                'type': 'info',
                'area': 'Talk Time',
                'message': f'Student spoke {student_pct}% - acceptable but aim for 40%+.'
            })
        
        # Vocabulary calibration
        vocab_cal = cast(dict[str, object], comparison.get('vocabulary_calibration', {}))
        ratio = cast(float, vocab_cal.get('teacher_to_student_ratio', 0))
        if ratio > 3:
            feedback.append({
                'type': 'warning',
                'area': 'Vocabulary Level',
                'message': f'Your vocabulary range is {ratio}x the student\'s. Consider simplifying.'
            })
        elif ratio >= 1.5 and ratio <= 2.5:
            feedback.append({
                'type': 'positive',
                'area': 'Vocabulary Level',
                'message': f'Good calibration! Your vocabulary is {ratio}x the student\'s - perfect for i+1.'
            })
        elif ratio > 0 and ratio < 1.5:
            feedback.append({
                'type': 'positive',
                'area': 'Vocabulary Match',
                'message': f'Vocabulary well-matched to student level (ratio: {ratio}x).'
            })
        
        # Speaking rate
        rate_diff = cast(float, cast(dict[str, object], comparison.get('speaking_rate_comparison', {})).get('difference', 0))
        if rate_diff > 40:
            feedback.append({
                'type': 'warning',
                'area': 'Speaking Speed',
                'message': f'You spoke {rate_diff} WPM faster than the student. Consider slowing down.'
            })
        elif abs(rate_diff) <= 20:
            feedback.append({
                'type': 'positive',
                'area': 'Speaking Speed',
                'message': f'Well-paced! Your speaking rate was within 20 WPM of the student.'
            })
        elif rate_diff < 0:
            feedback.append({
                'type': 'positive',
                'area': 'Speaking Speed',
                'message': f'Student spoke faster than you - sign of confidence!'
            })
        
        # Turn balance
        student_turns_pct = cast(float, cast(dict[str, object], comparison.get('turn_balance', {})).get('student_percentage', 0))
        if student_turns_pct >= 40:
            feedback.append({
                'type': 'positive',
                'area': 'Turn Taking',
                'message': f'Good conversational flow - student took {student_turns_pct}% of turns.'
            })

        return {
            'feedback_items': feedback,
            'overall_score': self._calculate_teaching_score(comparison)
        }

    def _calculate_teaching_score(self, comparison: dict[str, object]) -> int:
        """Calculate a simple 1-10 teaching effectiveness score"""
        score = 7  # Start neutral
        
        talk_ratio = cast(dict[str, object], comparison.get('talk_time_ratio', {}))
        student_pct = cast(float, talk_ratio.get('student_percentage', 0))
        if 40 <= student_pct <= 70:
            score += 1
        elif student_pct < 25:
            score -= 2
        
        vocab_cal = cast(dict[str, object], comparison.get('vocabulary_calibration', {}))
        ratio = cast(float, vocab_cal.get('teacher_to_student_ratio', 0))
        if 1.2 <= ratio <= 2.5:
            score += 1
        elif ratio > 4:
            score -= 1
        
        return max(1, min(10, score))

    def analyze_vocabulary(self) -> dict[str, object]:
        """Analyze vocabulary using lemmas for all speakers."""
        if not textblob_available or TextBlob is None:
            return {'error': 'TextBlob not available. Cannot perform vocabulary analysis.'}

        teacher_label = None
        for label, name in self.speaker_map.items():
            if name == self.teacher_name:
                teacher_label = label
                break
        
        student_words: list[str] = []
        for turn in self.student_turns_list:
            student_words.extend([str(w.get('text', '')).lower() for w in cast(list[dict[str, object]], turn.get('words', []))])

        teacher_words: list[str] = []
        if teacher_label:
            teacher_turns = self._get_turns_for_speaker(str(teacher_label))
            for turn in teacher_turns:
                teacher_words.extend([str(w.get('text', '')).lower() for w in cast(list[dict[str, object]], turn.get('words', []))])

        student_lemmas: set[str] = {self.lexical_engine.lemmatize(word) for word in student_words if word.isalpha()}
        teacher_lemmas: set[str] = {self.lexical_engine.lemmatize(word) for word in teacher_words if word.isalpha()}
        
        combined_lemmas = student_lemmas.union(teacher_lemmas)

        return {
            'student_unique_lemmas': len(student_lemmas),
            'teacher_unique_lemmas': len(teacher_lemmas),
            'combined_unique_lemmas': len(combined_lemmas),
            'student_teacher_lemma_overlap': len(student_lemmas.intersection(teacher_lemmas)),
        }

    # --- Session-Wide (Mixed) Data ---
    def _get_marked_turns_summary(self) -> dict[str, object]:
        """Summary of marked turns (all speakers)"""
        marked = [t for t in self.turns if cast(bool, t.get('marked', False))]
        return {
            'total_marked': len(marked),
            'marked_turns': [{
                'turn_order': cast(int, t.get('turn_order', 0)),
                'speaker': self.speaker_map.get(str(t.get('speaker', 'Unknown')), t.get('speaker', 'Unknown')),
                'mark_type': cast(str, t.get('mark_type', '')),
                'transcript': cast(str, t.get('transcript', ''))
            } for t in marked]
        }

    def _get_action_items(self) -> dict[str, object]:
        """Extract action items (all speakers)"""
        action_items_raw = self.session.get('action_items', [])
        action_items_named = [
            {
                "turn_order": cast(int, item.get('turn_order', 0)),
                "speaker": self.speaker_map.get(str(item.get('speaker', 'Unknown')), item.get('speaker', 'Unknown')),
                "transcript": cast(str, item.get('transcript', ''))
            } for item in cast(list[dict[str, object]], action_items_raw)
        ]
        return {
            "total_action_items": len(action_items_named),
            "action_items": action_items_named
        }

# --- Main execution ---
def analyze_session_file(session_file: Path) -> dict[str, object]:
    try:
        with open(session_file, 'r') as f:
            session_data = cast(dict[str, object], json.load(f))
    except Exception as e:
        logger.error(f"Failed to load session file: {session_file}. Error: {e}")
        sys.exit(1)

    analyzer = SessionAnalyzer(session_data)
    return analyzer.analyze_all()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python session_analyzer.py <session_file.json>")
        print("This script is now called automatically by main.py")
        sys.exit(1)

    session_file = Path(sys.argv[1])
    logger.info(f"--- Running Fast & Free Analysis on {session_file.name} ---")
    results = analyze_session_file(session_file)

    # Save analysis to session_..._analysis.json
    output_file = session_file.parent / f"{session_file.stem}_analysis.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ (Free) Analysis saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save analysis file: {output_file}. Error: {e}")
        sys.exit(1)
