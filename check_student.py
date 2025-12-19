
import json
import glob
import os

list_of_files = glob.glob('/Users/safeSpacesBro/AssemblyAIv2/sessions/*.json')
if not list_of_files:
    print("No files found")
    exit()
    
latest_file = max(list_of_files, key=os.path.getctime)
print(f"Reading: {latest_file}")

try:
    with open(latest_file, 'r') as f:
        data = json.load(f)
        # Look for student name in metadata or heuristic
        # Usually stored as 'student_name' or inferred from speakers
        print(f"Keys: {list(data.keys())}")
        if 'student_name' in data:
             print(f"Student: {data['student_name']}")
        else:
             print("No 'student_name' key found.")
             # Check turns for speaker names
             speakers = set()
             for t in data.get('turns', []):
                 speakers.add(t.get('speaker', 'Uk'))
             print(f"Speakers found: {speakers}")
except Exception as e:
    print(f"Error: {e}")
