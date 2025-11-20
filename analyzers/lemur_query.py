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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Load API key from environment
api_key = os.getenv('ASSEMBLYAI_API_KEY')
if not api_key:
    logger.error("❌ ASSEMBLYAI_API_KEY not found in environment. Cannot run LeMUR.")
    sys.exit(1)

aai.settings.api_key = api_key

def run_lemur_query(session_file: Path):
    """
    Loads a session, extracts the student-only text,
    runs the custom LeMUR query, and saves the response.
    """

    # 1. Load the session.json file (This contains the full transcript)
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"LeMUR: Failed to load session file: {session_file}. Error: {e}")
        sys.exit(1)

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
        sys.exit(1)

    if not lemur_prompt:
        logger.error("LeMUR: No custom prompt found in session file. Aborting.")
        sys.exit(1)

    # 3. Refine the prompt (Add context about the student)
    # This is important for context and specificity
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
            logger.error("LeMUR: session_id not found in session file. Cannot use transcript_ids. Aborting.")
            sys.exit(1)

        logger.info(f"LeMUR: Using transcript ID for analysis: {transcript_id}")

        result = aai.Lemur.task(
            prompt=full_lemur_prompt,
            final_model='default',
            transcript_ids=[transcript_id] # Use the transcript ID for auto-chunking
        )

        lemur_response = result.response

    except Exception as e:
        logger.error(f"LeMUR: API call failed. Check credits and API key validity. Error: {e}")
        sys.exit(1)

def run_lemur_query(session_file: Path) -> Dict[str, Any]:
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
        sys.exit(1)

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
        sys.exit(1)

    if not lemur_prompt:
        logger.error("LeMUR: No custom prompt found in session file. Aborting.")
        sys.exit(1)

    # 3. Refine the prompt (Add context about the student)
    # This is important for context and specificity
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
            logger.error("LeMUR: session_id not found in session file. Cannot use transcript_ids. Aborting.")
            sys.exit(1)

        logger.info(f"LeMUR: Using transcript ID for analysis: {transcript_id}")

        result = aai.Lemur.task(
            prompt=full_lemur_prompt,
            final_model='default',
            transcript_ids=[transcript_id] # Use the transcript ID for auto-chunking
        )

        lemur_response = result.response

    except Exception as e:
        logger.error(f"LeMUR: API call failed. Check credits and API key validity. Error: {e}")
        sys.exit(1)

    # Load the existing analysis data (created by session_analyzer.py)
    analysis_file = session_file.parent / f"{session_file.stem}_analysis.json"
    analysis_data = {}
    if analysis_file.exists():
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
        except Exception as e:
            logger.warning(f"LeMUR: Failed to load existing analysis file: {analysis_file}. Error: {e}. Starting with empty analysis_data.")

    # Add the new LeMUR block
    analysis_data['lemur_analysis'] = {
        'prompt': lemur_prompt,
        'response': lemur_response,
        'model': result.model,
        'cost_estimate': 'See AssemblyAI pricing dashboard'
    }

    # --- NEW: Action Item Extraction ---
    action_item_prompt = (
        "You are an AI assistant tasked with identifying action items from a conversation transcript. "
        "For each speaker, identify any commitments or tasks they explicitly state they will perform. "
        "Look for phrases like 'I will', 'I'm going to', 'I'll work on', 'I'll put together', 'I'll develop', "
        "'I'll think about', 'Let me [verb]'. List each action item, clearly stating who committed to it. "
        "If no action items are found, state 'No action items identified.'"
    )
    logger.info("LeMUR: Running action item extraction...")
    action_items_result = aai.Lemur.task(
        prompt=action_item_prompt,
        final_model='default',
        transcript_ids=[transcript_id]
    )
    analysis_data['action_items_analysis'] = {
        'prompt': action_item_prompt,
        'response': action_items_result.response,
        'model': action_items_result.model,
        'cost_estimate': 'See AssemblyAI pricing dashboard'
    }
    logger.info("✅ (Paid) LeMUR action item analysis completed.")
    # --- END NEW ---

    # Print the response to the terminal so the user sees it instantly
    print("\n" + "="*60)
    print(f"LeMUR RESPONSE for '{lemur_prompt}':")
    print("="*60)
    print(lemur_response)
    print("="*60 + "\n")

    # Print action items to terminal
    print("\n" + "="*60)
    print("ACTION ITEMS IDENTIFIED:")
    print("="*60)
    print(action_items_result.response)
    print("="*60 + "\n")

    return analysis_data


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
