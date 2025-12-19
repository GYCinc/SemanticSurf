#!/usr/bin/env python3
"""
LeMUR Deep-Dive Analysis (PAID)
Runs a custom LeMUR query on ONLY the student's text.
Augments the existing _analysis.json file.
"""

import assemblyai as aai
import os
import sys
import json
from pathlib import Path
import logging
from typing import Dict, Any
import requests # Use requests for synchronous calls since this script is sync

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Load API key from environment
api_key = os.getenv('ASSEMBLYAI_API_KEY')
if not api_key:
    logger.error("❌ ASSEMBLYAI_API_KEY not found in environment. Cannot run LeMUR.")
    sys.exit(1)

aai.settings.api_key = api_key

def run_lemur_query(session_file: Path, analysis_context: Dict[str, Any] = None):
    """
    Loads a session, extracts text,
    runs the LLM Gateway query (Claude Sonnet 3.5),
    and returns the analysis data.
    
    Args:
        session_file: Path to the session.json
        analysis_context: Optional dictionary containing pre-calculated metrics 
                          (POS, N-grams, Comparative stats) to inject into the prompt.
    """

    # 1. Load the session.json file (This contains the full transcript)
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"LeMUR: Failed to load session file: {session_file}. Error: {e}")
        return {"error": "Failed to load session file", "response": str(e)}

    # 2. Get Student's label
    speaker_map = session_data.get('speaker_map', {})
    student_name = session_data.get('student_name', 'Student')
    
    # --- Context Injection ---
    context_string = ""
    if analysis_context:
        # Format the context into a readable block for the LLM
        context_string = "\n\n## 📊 Pre-Calculated Linguistic Metrics (TRUST THESE OVER GUESSES)\n"
        
        # 1. Comparative Context (Tutor vs Student)
        if 'comparison' in analysis_context:
            comp = analysis_context['comparison']
            talk_ratio = comp.get('talk_time_ratio', {}).get('student_percentage', 0)
            vocab_ratio = comp.get('vocabulary_calibration', {}).get('teacher_to_student_ratio', 0)
            overlap = comp.get('tutor_overlap_pct', 0)
            
            context_string += f"- **Talk Time**: Student spoke {talk_ratio}% of the time.\n"
            context_string += f"- **Vocabulary**: Tutor uses {vocab_ratio}x more unique words than Student.\n"
            context_string += f"- **Tutor Overlap**: {overlap}% of student's phrases matched yours (fluency benchmark).\n"

        # 2. CAF Metrics (Complexity, Accuracy, Fluency)
        if 'caf_metrics' in analysis_context:
            caf = analysis_context['caf_metrics']
            if caf:
                # Safely access nested keys
                mlt = caf.get('complexity', {}).get('mean_length_t_unit', 0)
                mlr = caf.get('fluency', {}).get('mean_length_run', 0)
                pause_rate = caf.get('fluency', {}).get('filled_pause_rate_per_100', 0)
                
                context_string += f"- **Complexity (MLT)**: {mlt} (Higher is better for C1+)\n"
                context_string += f"- **Fluency (MLR)**: {mlr} words between pauses.\n"
                context_string += f"- **Hesitation**: {pause_rate} filled pauses per 100 words.\n"

        # 3. Register (Amalgum)
        if 'register_analysis' in analysis_context:
            reg = analysis_context['register_analysis']
            context_string += f"- **Register**: {reg.get('classification', 'Unknown')} (Academic: {reg.get('scores', {}).get('academic', 0)}, Casual: {reg.get('scores', {}).get('conversational', 0)})\n"

        # 4. Detected Errors (Pattern Matching)
        if 'detected_errors' in analysis_context:
            errs = analysis_context['detected_errors']
            context_string += f"- **Pattern-Matched Errors**: {len(errs)} found (Check these for confirmation).\n"
            # List first 5 for context
            for i, err in enumerate(errs[:5]):
                context_string += f"  - {err.get('error_type')}: '{err.get('text')}'\n"

    # 3. Construct System Prompt (Unified with ingest_audio.py + Context)
    system_prompt = f"""You are an expert applied linguist and instructional designer. The user will provide a transcript of a one-on-one English tutoring session between a tutor (named "Aaron") and a student. Your task is to analyze the student's spoken language, identify systematic errors (especially those that appear fossilized), and produce a personalized, prioritized to-do list to help the student improve.

{context_string}

## Instructions

1. **Identify the student's lines**  
   - The tutor is always labeled "Aaron". All other speech belongs to the student. Ignore the tutor's utterances for error analysis (they may be used only for context).

2. **Extract and categorize errors**  
   - Read each student utterance carefully.  
   - For each error, determine whether it is a **systematic error** (repeated, pattern‑based) or a **slip** (one‑off mistake). Focus on systematic errors; ignore slips unless they are frequent.  
   - Categorize each systematic error as one of:  
     - **Syntax** – includes word order, clause structure, and morphological issues (verb tense, aspect, agreement, articles, plurals, etc.)  
     - **Lexis** – word choice, collocations, idioms, preposition use  
     - **Pragmatics** – register, politeness, cultural appropriateness, conversational strategies  
   - Note the exact utterance, a corrected version, the category, and a brief linguistic explanation (e.g., L1 interference, overgeneralization).

3. **Estimate the student's CEFR level**  
   - Based on the overall complexity, range, and accuracy of the language, assign a CEFR level (A1, A2, B1, B2, C1, C2). Provide a short justification in your reasoning.

4. **Select the top three errors**  
   - Evaluate the impact of each systematic error on communication. Consider frequency, comprehensibility, and potential for misunderstanding.  
   - Choose **up to three** errors that are most detrimental. If there are fewer than three systematic errors, select all of them.

5. **Design specific remedial tasks**  
   - For each selected error, create **one concrete, actionable task** the student can do to address that error.  
   - Tasks must be specific (e.g., "Complete 10 gap‑fill exercises on the present perfect vs. simple past", "Use flashcards to practice collocations with 'make' and 'do'", "Record yourself making polite requests and compare with native speaker examples").  
   - Avoid vague advice like "study grammar" or "watch movies".

6. **Assign priorities**  
   - Assign each task a priority based on how urgently it should be addressed:  
     - **HIGH** – the error severely impedes understanding; address immediately.  
     - **MEDIUM** – the error is noticeable but less critical; address after high‑priority items.  
     - **LOW** – the error is minor or stylistic; address once higher priorities are handled.  
   - Use only the labels "HIGH", "MEDIUM", or "LOW" for the `priority` field.

7. **Prepare the final JSON output**  
   - Construct a JSON object **exactly** following the schema below.  
   - Do not include any extra text, commentary, or markdown formatting outside the JSON.  
   - Ensure the JSON is valid (use double quotes, escape characters properly).  
   - The JSON must contain exactly the fields described; do not add extra keys.

## Output Schema

```json
{{
  "student_profile": {{
    "cefr_estimate": "CEFR level (e.g., B1)",
    "dominant_issue": "A concise description of the most prominent systematic error pattern"
  }},
  "internal_reasoning": "A short paragraph explaining your analysis: why you chose these errors, how you estimated the CEFR level, and any other relevant observations.",
  "annotated_errors": [
    {{
      "quote": "The exact student utterance containing the error",
      "correction": "A native‑like version of the utterance",
      "linguistic_category": "Syntax / Lexis / Pragmatics",
      "explanation": "Brief linguistic description (e.g., 'L1 transfer causing omission of articles')"
    }}
  ],
  "prioritized_to_do_list": [
    {{
      "priority": "HIGH",
      "task": "Specific, actionable task description",
      "reason": "Explanation of how this task addresses the corresponding error"
    }}
  ]
}}
```
"""

    # 4. Construct Transcript
    full_transcript_text = "\n".join([
        f"{turn.get('speaker', 'Unknown')}: {turn.get('transcript', '')}" 
        for turn in session_data.get('turns', [])
    ])
    
    logger.info(f"LeMUR: Analyzing turns from '{student_name}'.")

    # 5. Call LLM Gateway
    try:
        llm_gateway_url = "https://llm-gateway.assemblyai.com/v1/chat/completions"
        llm_payload = {
            "model": "gemini-1.5-pro", # Balanced choice: High intelligence, good speed
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please analyze the following transcript:\n\n{full_transcript_text}"}
            ],
            "max_tokens": 8000
        }
        
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(llm_gateway_url, json=llm_payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        llm_result = response.json()
        
        # Extract Content
        choices = llm_result.get("choices", [])
        llm_content = ""
        if choices and len(choices) > 0:
            llm_content = choices[0].get("message", {}).get("content", "")
            
        # Parse JSON from content
        clean_content = llm_content.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(clean_content)
        
        # Map to Legacy Format + New Data
        return {
            "lemur_analysis": {
                "response": parsed_data.get("internal_reasoning", llm_content), # Legacy field
                "student_profile": parsed_data.get("student_profile"),
                "annotated_errors": parsed_data.get("annotated_errors"),
                "prioritized_to_do_list": parsed_data.get("prioritized_to_do_list"),
                "request_id": llm_result.get("id"),
                "usage": str(llm_result.get("usage"))
            }
        }

    except Exception as e:
        logger.error(f"LLM Gateway Failed: {e}")
        return {"error": "API call failed", "response": str(e)}



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python lemur_query.py <session_file.json>")
        sys.exit(1)

    session_file = Path(sys.argv[1])
    logger.info(f"--- Running LeMUR Deep Analysis on {session_file.name} ---")
    
    # Call the function and get the analysis data
    final_analysis_data = run_lemur_query(session_file)

    # Save the returned data to the file
    output_file = session_file.parent / f"{session_file.stem}_analysis.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_analysis_data, f, indent=2)
        logger.info(f"✅ (Paid) LeMUR analysis saved to: {output_file}")
    except Exception as e:
        logger.error(f"LeMUR: Failed to save analysis to {output_file}: {e}")
        sys.exit(1)