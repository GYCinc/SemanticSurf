import re
import csv
import os

# Configuration
INPUT_DIR = '/Users/safeSpacesBro/AssemblyAIv2/ErrorCorp'
OUTPUT_FILE = '/Users/safeSpacesBro/AssemblyAIv2/ErrorCorp/new_linguistic_phenomena.csv'

# File filenames
FILE_100_RULES = '433417160-100-Golden-Rules-of-English-Grammar-for-Error-Detection.txt'
FILE_650_ERRORS = '361467272-650-Common-Error.txt'
FILE_PREPOSITIONS = '793835222-preposition-errors.txt'

def clean_text(text):
    """Cleans up whitespace and unnecessary characters."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def append_to_csv(data_rows):
    """Appends specific rows to the CSV file."""
    # Columns: itemName,publicCategory,errorScope,errorType,subcategory,triggerPattern,exampleErrors,exampleCorrections,cefrLevel,severity,l1Interference
    
    file_exists = os.path.isfile(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Assuming header already exists from previous steps, so we just append
        # If file doesn't exist, we should probably add header, but the plan says append to existing.
        # Let's check if it's empty just in case.
        if not file_exists or os.stat(OUTPUT_FILE).st_size == 0:
             writer.writerow(['itemName', 'publicCategory', 'errorScope', 'errorType', 'subcategory', 'triggerPattern', 'exampleErrors', 'exampleCorrections', 'cefrLevel', 'severity', 'l1Interference'])

        for row in data_rows:
            writer.writerow(row)
    print(f"Appended {len(data_rows)} rows to {OUTPUT_FILE}")

def parse_100_rules():
    print(f"Parsing {FILE_100_RULES}...")
    filepath = os.path.join(INPUT_DIR, FILE_100_RULES)
    extracted = []
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Pattern: 
    # Incorrect- ...
    # Correct- ...
    # This file sometimes has numbers or headings in between.
    
    # We'll split by "Incorrect-" to find blocks
    parts = re.split(r'Incorrect[-:]', content)
    
    for part in parts[1:]: # Skip preamble
        # Each part should start with the incorrect sentence, then have "Correct-" somewhere
        if 'Correct' not in part:
            continue
            
        # Split into incorrect and remainder
        split_part = re.split(r'Correct[-:]', part, maxsplit=1)
        if len(split_part) < 2:
            continue
            
        incorrect_sent = clean_text(split_part[0])
        remainder = split_part[1]
        
        # The correct sentence is usually the first line or up to the next number/heading
        # Heuristic: Take the first sentence or line from remainder
        correct_sent_match = re.search(r'^(.*?)(?=\n\n|\r\n\r\n|\d+\.|$)', remainder, re.DOTALL)
        if correct_sent_match:
            correct_sent = clean_text(correct_sent_match.group(1))
        else:
            correct_sent = clean_text(remainder.split('\n')[0])

        if incorrect_sent and correct_sent:
            extracted.append([
                'Golden Rule Error',           # itemName
                'Grammar',                     # publicCategory
                'Sentence',                    # errorScope
                'General Grammar',             # errorType
                'Rule-based',                  # subcategory
                '',                            # triggerPattern
                incorrect_sent,                # exampleErrors
                correct_sent,                  # exampleCorrections
                'B1',                          # cefrLevel
                'Medium',                      # severity
                ''                             # l1Interference
            ])
            
    print(f"Found {len(extracted)} items in 100 Rules.")
    return extracted

def parse_650_errors():
    print(f"Parsing {FILE_650_ERRORS}...")
    filepath = os.path.join(INPUT_DIR, FILE_650_ERRORS)
    extracted = []

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Format is tricky. 
    # 1. ... (Question)
    # (a) ... (b) ... (c) ... (d) ... (Parts of sent sometimes)
    # Ans (1): (c) Explanation... Correct Sentence.
    
    # Actually, looking at the file view from history:
    # 1.  I have not (a) / seen him since (b) / twenty years (c) / and so I cannot say with certainty whether he is alive or dead (d) / No error (e)
    # Ans (1): (c) 'for' should be used in place of 'since' ...
    
    # We need to extract the "sentence" from line 1 (stripping a/b/c identifiers)
    # And the correction/explanation from the Ans line.

    current_question = ""
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Detect Question (Start with number)
        if re.match(r'^\d+\.', line):
            # Clean up the (a) / (b) stuff to make a readable bad sentence
            raw_q = re.sub(r'^\d+\.', '', line).strip()
            # Remove (a), (b), / etc
            clean_q = re.sub(r'\([a-e]\)', '', raw_q)
            clean_q = re.sub(r'\s+/\s+', ' ', clean_q)
            clean_q = clean_q.replace('No error', '').strip()
            current_question = clean_q
            
        # Detect Answer
        elif line.startswith('Ans'):
            if not current_question:
                continue
                
            explanation = line
            # Extract simple correction if possible, often after a colon or just the whole text
            # The 'explanation' is often "Replace X with Y" or similar.
            # We will put the explanation in 'exampleCorrections' for now, or try to infer.
            # The user asked for "Answer's right", which implies the text contains the fix.
            # Since generating the perfect corrected sentence programmatically is hard without LLM,
            # we will store the Explanation in 'exampleCorrections' column for the user to review, 
            # OR we store the original bad sentence + the explanation.
            
            clean_ans = clean_text(re.sub(r'^Ans.*?:', '', line))
            
            extracted.append([
                'Common Error 650',            # itemName
                'Grammar',                     # publicCategory
                'Sentence',                    # errorScope
                'Common Usage',                # errorType
                'Exam Error',                  # subcategory
                '',                            # triggerPattern
                current_question,              # exampleErrors
                clean_ans,                     # exampleCorrections (Explanation in this case)
                'B2',                          # cefrLevel
                'High',                        # severity
                ''                             # l1Interference
            ])
            current_question = "" # Reset

    print(f"Found {len(extracted)} items in 650 Errors.")
    return extracted

def parse_prepositions():
    print(f"Parsing {FILE_PREPOSITIONS}...")
    filepath = os.path.join(INPUT_DIR, FILE_PREPOSITIONS)
    extracted = []
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        
    # Pattern:
    # Incorrect: ...
    # Correct: ...
    
    parts = re.split(r'Incorrect:', content)
    for part in parts[1:]:
        if 'Correct:' not in part:
            continue
            
        split_part = re.split(r'Correct:', part, maxsplit=1)
        if len(split_part) < 2:
            continue
            
        incorrect = clean_text(split_part[0])
        remainder = split_part[1]
        
        # Take first line of remainder as correct
        correct = clean_text(remainder.split('\n')[0])
        
        if incorrect and correct:
             extracted.append([
                'Preposition Error',           # itemName
                'Grammar',                     # publicCategory
                'Phrase',                      # errorScope
                'Prepositions',                # errorType
                'Usage',                       # subcategory
                '',                            # triggerPattern
                incorrect,                     # exampleErrors
                correct,                       # exampleCorrections
                'A2',                          # cefrLevel
                'Medium',                      # severity
                ''                             # l1Interference
            ])

    print(f"Found {len(extracted)} items in Prepositions.")
    return extracted

def main():
    all_data = []
    all_data.extend(parse_100_rules())
    all_data.extend(parse_650_errors())
    all_data.extend(parse_prepositions())
    
    if all_data:
        append_to_csv(all_data)
        print("Success!")
    else:
        print("No data extracted.")

if __name__ == "__main__":
    main()
