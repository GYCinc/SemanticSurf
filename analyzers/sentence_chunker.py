import os
import re
import json
from typing import List, Dict, Any, Optional

def chunk_transcript(file_path_or_text: str, max_chunk_chars: int = 3000, sentence_overlap: int = 2) -> List[str]:
    """
    Splits a transcript into overlapping chunks based on sentence boundaries.
    Supports either a file path or direct string input.
    """
    sentences = []
    
    # Check if input is a path
    if os.path.exists(file_path_or_text):
        if file_path_or_text.endswith('.json'):
            try:
                with open(file_path_or_text, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if 'sentences' in data: sentences = [s['text'] for s in data['sentences']]
                        elif 'text' in data: sentences = re.split(r'(?<=[.!?])\s+', data['text'])
                    elif isinstance(data, list):
                        full_text = " ".join([w.get('text', '') for w in data])
                        sentences = re.split(r'(?<=[.!?])\s+', full_text)
            except Exception: pass
        else:
            try:
                with open(file_path_or_text, 'r', encoding='utf-8') as f:
                    text = f.read()
                sentences = re.split(r'(?<=[.!?])\s+', text)
            except Exception: pass
    
    # If not a path or file read failed, treat as raw text
    if not sentences:
        sentences = re.split(r'(?<=[.!?])\s+', file_path_or_text)

    chunks = []
    current_chunk_sentences = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence: continue
        
        if current_length + len(sentence) > max_chunk_chars and current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            overlap = current_chunk_sentences[-sentence_overlap:] if sentence_overlap > 0 else []
            current_chunk_sentences = overlap
            current_length = sum(len(s) + 1 for s in overlap)
            
        current_chunk_sentences.append(sentence)
        current_length += len(sentence) + 1
        
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    return chunks
