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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Load API key from environment
api_key = os.getenv('ASSEMBLYAI_API_KEY')
if not api_key:
    logger.error("❌ ASSEMBLYAI_API_KEY not found in environment. Cannot run LeMUR.")
    sys.exit(1)

aai.settings.api_key = api_key

def run_lemur_query(session_file: Path, custom_prompt: str = None):
    """
    Loads a session, extracts the student-only text,
    runs the custom LeMUR query, and returns the analysis data.
    """

    # 1. Load the session.json file (This contains the full transcript)
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"LeMUR: Failed to load session file: {session_file}. Error: {e}")
        return {"error": "Failed to load session file", "response": str(e)}

    # 2. Get Student's label and custom prompt from the saved data
    speaker_map = session_data.get('speaker_map', {})
    student_name = session_data.get('student_name', 'Student')
    lemur_prompt = session_data.get('lemur_prompt')

    student_label = None
    for label, name in speaker_map.items():
        if name == student_name:
            student_label = label
            break

    if not student_label:
        logger.error("LeMUR: Could not find student label. Aborting.")
        return {"error": "Student label not found", "response": "Could not find student label in speaker map"}

    if custom_prompt:
        lemur_prompt = custom_prompt
    elif not lemur_prompt:
        logger.error("LeMUR: No custom prompt found in session file. Using default.")
        lemur_prompt = "Analyze this student conversation for language learning insights."

    # 3. Refine the prompt (Add context about the student)
    full_lemur_prompt = (
        f"You are an expert ESL tutor analyzing a conversation between a tutor and a student. "
        f"The student's name is '{student_name}'. Please focus your analysis on the student's speech. "
        f"Answer the following question based on the student's language use: "
        f"**{lemur_prompt}**"
    )

    logger.info(f"LeMUR: Analyzing turns from '{student_name}'.")

    # 5. Run the LeMUR query (using the full transcript for auto-chunking)
    try:
        # Use the session_id as the transcript_id for LeMUR
        transcript_id = session_data.get('session_id')
        if not transcript_id:
            logger.error("LeMUR: session_id not found in session file. Cannot use transcript_ids.")
            return {"error": "No session ID", "response": "Session ID not found in file"}

        logger.info(f"LeMUR: Using transcript ID for analysis: {transcript_id}")

        # Construct full input text from session data for LeMUR
        input_text = ""
        for turn in session_data.get('turns', []):
            speaker = turn.get('speaker', 'Unknown')
            text = turn.get('transcript', '')
            input_text += f"{speaker}: {text}\n"

        result = aai.Lemur.task(
            prompt=full_lemur_prompt,
            final_model='default',
            input_text=input_text 
        )

        lemur_response = result.response

        # Return the analysis data structure expected by main.py
        return {
            "lemur_analysis": {
                "response": lemur_response,
                "model": result.model,
                "cost_estimate": "See AssemblyAI pricing dashboard"
            }
        }

    except Exception as e:
        logger.error(f"LeMUR: API call failed. Check credits and API key validity. Error: {e}")
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