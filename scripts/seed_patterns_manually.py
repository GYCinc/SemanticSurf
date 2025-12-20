"""
Seed Patterns Manually (Cold Start)

Since the LLM API is rate-limited, this script generates a representative
"Seed Set" of error patterns for the 80 Cambridge Error Codes using
deterministic linguistic rules and known common learner errors.

This ensures the system is "up to date" with the new schema and functional,
even without the 100k LLM-generated dataset.
"""

import json
import os

OUTPUT_FILE = 'data/generated_patterns.json'

def get_seed_patterns():
    return {
        "#RT": [ # Replace Preposition
            {"incorrect": "depend of", "correct": "depend on"},
            {"incorrect": "married with", "correct": "married to"},
            {"incorrect": "interested on", "correct": "interested in"},
            {"incorrect": "arrive to", "correct": "arrive at"},
            {"incorrect": "spend money in", "correct": "spend money on"}
        ],
        "#MD": [ # Missing Determiner
            {"incorrect": "I have car", "correct": "I have a car"},
            {"incorrect": "in morning", "correct": "in the morning"},
            {"incorrect": "he is teacher", "correct": "he is a teacher"},
            {"incorrect": "sun is hot", "correct": "the sun is hot"},
            {"incorrect": "play piano", "correct": "play the piano"}
        ],
        "#TV": [ # Tense Verb
            {"incorrect": "I have seen him yesterday", "correct": "I saw him yesterday"},
            {"incorrect": "I am living here since 2010", "correct": "I have lived here since 2010"},
            {"incorrect": "If I will go", "correct": "If I go"},
            {"incorrect": "I didn't went", "correct": "I didn't go"},
            {"incorrect": "He has arrived last week", "correct": "He arrived last week"}
        ],
        "#S": [ # Spelling
            {"incorrect": "becuase", "correct": "because"},
            {"incorrect": "wich", "correct": "which"},
            {"incorrect": "goverment", "correct": "government"},
            {"incorrect": "beautifull", "correct": "beautiful"},
            {"incorrect": "thier", "correct": "their"}
        ],
        "#W": [ # Word Order
            {"incorrect": "I like very much it", "correct": "I like it very much"},
            {"incorrect": "She is enough old", "correct": "She is old enough"},
            {"incorrect": "I have always time", "correct": "I always have time"},
            {"incorrect": "Is ready the breakfast?", "correct": "Is the breakfast ready?"},
            {"incorrect": "I explain you the problem", "correct": "I explain the problem to you"}
        ],
        "#FV": [ # Form Verb
            {"incorrect": "I enjoy to swim", "correct": "I enjoy swimming"},
            {"incorrect": "I look forward to see you", "correct": "I look forward to seeing you"},
            {"incorrect": "I can to go", "correct": "I can go"},
            {"incorrect": "She make me cry", "correct": "She makes me cry"},
            {"incorrect": "We suggested to go", "correct": "We suggested going"}
        ],
        "#CN": [ # Countability Noun
            {"incorrect": "informations", "correct": "information"},
            {"incorrect": "advices", "correct": "advice"},
            {"incorrect": "furnitures", "correct": "furniture"},
            {"incorrect": "homeworks", "correct": "homework"},
            {"incorrect": "a news", "correct": "some news"}
        ],
        "#RP": [ # Replace Punctuation
            {"incorrect": "However he didn't come", "correct": "However, he didn't come"},
            {"incorrect": "Its a nice day", "correct": "It's a nice day"},
            {"incorrect": "dogs bone", "correct": "dog's bone"},
            {"incorrect": "cats tails", "correct": "cats' tails"},
            {"incorrect": "Who is it.", "correct": "Who is it?"}
        ],
        "#AS": [ # Argument Structure
            {"incorrect": "I explained him the rule", "correct": "I explained the rule to him"},
            {"incorrect": "She said me that", "correct": "She told me that"},
            {"incorrect": "I suggest you to go", "correct": "I suggest that you go"},
            {"incorrect": "Describe me the picture", "correct": "Describe the picture to me"},
            {"incorrect": "He recommended me the book", "correct": "He recommended the book to me"}
        ],
        "#ID": [ # Idiom
            {"incorrect": "make a party", "correct": "have a party"},
            {"incorrect": "take a coffee", "correct": "have a coffee"},
            {"incorrect": "in the end of the day", "correct": "at the end of the day"},
            {"incorrect": "make a question", "correct": "ask a question"},
            {"incorrect": "do a mistake", "correct": "make a mistake"}
        ]
    }

def main():
    print(f"🌱 Seeding Pattern Database manually...")
    
    seed_data = get_seed_patterns()
    
    # Create the full structure
    full_db = {
        "metadata": {
            "source": "Manual Seed (Cold Start)",
            "version": "1.0",
            "count": sum(len(v) for v in seed_data.values())
        },
        "patterns": seed_data
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(full_db, f, indent=2)
        
    print(f"✅ Seeded {full_db['metadata']['count']} patterns across {len(seed_data)} categories.")
    print(f"💾 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
