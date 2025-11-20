#!/usr/bin/env python3
"""
Export Low-Confidence Words
Extracts all words with a confidence score below a specified threshold
from a session JSON file and saves them to a simple text file.
"""

import json
import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Load config to get the threshold
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    analysis_config = config.get('analysis_settings', {})
    CONFIDENCE_THRESHOLD = analysis_config.get('low_confidence_threshold', 0.5)
    logger.info(f"Using confidence threshold: {CONFIDENCE_THRESHOLD}")
except Exception as e:
    logger.warning(f"Could not load config.json. Using default threshold 0.5. Error: {e}")
    CONFIDENCE_THRESHOLD = 0.5


def export_low_confidence_words(session_file: Path):
    """
    Loads a session file, finds all words below the confidence threshold,
    and saves them to a text file.
    """
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load session file: {session_file}. Error: {e}")
        sys.exit(1)

    turns = session_data.get('turns', [])
    low_confidence_words = []

    for turn in turns:
        words = turn.get('words', [])
        for word in words:
            if word.get('confidence', 1.0) < CONFIDENCE_THRESHOLD:
                low_confidence_words.append({
                    "word": word.get('text'),
                    "confidence": word.get('confidence'),
                    "turn_order": turn.get('turn_order')
                })

    if not low_confidence_words:
        logger.info("No words found below the confidence threshold.")
        return

    # Save to a text file
    output_file = session_file.parent / f"{session_file.stem}_low_confidence_words.txt"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Words with confidence < {CONFIDENCE_THRESHOLD} from session {session_data.get('session_id')}\n")
            f.write("="*40 + "\n\n")
            for item in low_confidence_words:
                f.write(f"Word: \"{item['word']}\" (Confidence: {item['confidence']:.2f}) - (Turn {item['turn_order']})\n")
        
        logger.info(f"✅ Low-confidence words saved to: {output_file}")
        print(f"✅ Low-confidence words saved to: {output_file}")

    except Exception as e:
        logger.error(f"Failed to save low-confidence words file: {output_file}. Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python export_low_confidence_words.py <session_file.json>")
        sys.exit(1)

    session_file = Path(sys.argv[1])
    logger.info(f"--- Exporting low-confidence words from {session_file.name} ---")
    export_low_confidence_words(session_file)
