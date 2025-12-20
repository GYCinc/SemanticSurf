"""
Generate Pattern 100k Dataset

This script iterates through the 80 authoritative Cambridge Error Codes
and uses the LLM (via OpenRouter) to generate high-quality, specific
error patterns for each code.

It saves the results incrementally to 'data/generated_patterns.json'.
"""

import json
import os
import sys
from time import sleep
import re

# Add project root to path to import lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.openrouter_client import chat

ERROR_CODES_FILE = 'data/firecrawl_errors.json'
OUTPUT_FILE = 'data/generated_patterns.json'
PATTERNS_PER_BATCH = 5 # Number of examples to ask for per call
TARGET_PATTERNS_PER_CODE = 20 # Total patterns we want per code (starting small for testing)

# Limit for this run to avoid burning too many tokens if something goes wrong
# Set to None to run all
CODE_LIMIT = None 

def load_codes():
    with open(ERROR_CODES_FILE, 'r') as f:
        data = json.load(f)
    return data['codes']

def load_existing_patterns():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_patterns(patterns):
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(patterns, f, indent=2)

def generate_prompt(code_info):
    code = code_info['code']
    desc = code_info['description']
    category = code_info['category']
    
    prompt = f"""
    You are the "Priest" of the Cambridge Learner Corpus.
    
    Task: Generate {PATTERNS_PER_BATCH} specific, realistic learner error patterns for the following Cambridge Error Code:
    
    Code: {code}
    Category: {category}
    Description: {desc}
    
    Guidelines:
    1. Examples must be realistic mistakes made by English learners (ESL/EFL).
    2. Focus on high-frequency errors.
    3. Provide the 'Incorrect' phrase and the 'Correct' phrase.
    4. Do not provide full sentences, just the specific phrase pattern if possible, unless context is strictly required (like for Tense).
    
    Output Format (JSON only, list of objects):
    [
      {{ "incorrect": "...", "correct": "..." }},
      ...
    ]
    """
    return prompt

def clean_json_response(response_text):
    # Strip markdown code blocks if present
    response_text = re.sub(r'^```json', '', response_text)
    response_text = re.sub(r'^```', '', response_text)
    response_text = re.sub(r'```$', '', response_text)
    return response_text.strip()

def main():
    print(f"🔥 Starting Pattern Generation for {ERROR_CODES_FILE}")
    
    codes = load_codes()
    patterns_db = load_existing_patterns()
    
    # Initialize DB structure if new
    if 'metadata' not in patterns_db:
        patterns_db = {
            "metadata": {
                "source": "LLM Generation based on Cambridge Codes",
                "version": "1.0"
            },
            "patterns": {}
        }
    
    count = 0
    for i, code_obj in enumerate(codes):
        if CODE_LIMIT and count >= CODE_LIMIT:
            break
            
        code = code_obj['code']
        
        # Skip if we already have enough patterns for this code
        if code in patterns_db['patterns'] and len(patterns_db['patterns'][code]) >= TARGET_PATTERNS_PER_CODE:
            print(f"⏩ Skipping {code} (Already has {len(patterns_db['patterns'][code])} patterns)")
            continue
            
        print(f"⚡️ Generating patterns for {code} ({code_obj['description']})...")
        
        try:
            prompt = generate_prompt(code_obj)
            # Use a free model to avoid credit issues
            response = chat(prompt, model="google/gemini-2.0-flash-exp:free", temperature=0.7)
            
            cleaned_response = clean_json_response(response)
            
            new_patterns = json.loads(cleaned_response)
            
            if code not in patterns_db['patterns']:
                patterns_db['patterns'][code] = []
                
            patterns_db['patterns'][code].extend(new_patterns)
            
            # Save incrementally
            save_patterns(patterns_db)
            print(f"✅ Saved {len(new_patterns)} new patterns for {code}")
            
            count += 1
            # Sleep briefly to be nice to the rate limit
            sleep(1)
            
        except Exception as e:
            print(f"❌ Error generating for {code}: {e}")
            if 'response' in locals():
                print(f"Response was: {response[:100]}...")
            else:
                print("No response received.")
            
    print(f"🏁 Generation Complete. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
