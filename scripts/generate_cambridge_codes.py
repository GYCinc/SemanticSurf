import json

def generate_cambridge_codes():
    codes = []
    
    # 1. General types (First Letter) + Word classes (Second Letter)
    # Rules extracted from: "The majority of codes are based on a two-letter system..."
    general_types = {
        "F": "Wrong Form used",
        "M": "Something Missing",
        "R": "Word or phrase needs Replacing",
        "U": "Word or phrase is Unnecessary",
        "D": "Word is wrongly Derived"
    }
    
    word_classes = {
        "A": "Pronoun (Anaphoric)",
        "C": "Conjunction",
        "D": "Determiner",
        "J": "Adjective",
        "N": "Noun",
        "Q": "Quantifier",
        "T": "Preposition",
        "V": "Verb",
        "Y": "Adverb (-lY)"
    }
    
    for g_code, g_desc in general_types.items():
        for w_code, w_desc in word_classes.items():
            codes.append({
                "code": f"#{g_code}{w_code}",
                "category": f"{g_desc} - {w_desc}",
                "description": f"{g_desc} involving a {w_desc}"
            })

    # 2. Punctuation errors (Error type + P)
    # "MP punctuation Missing, RP punctuation needs Replacing, UP Unnecessary punctuation"
    punctuation_types = {
        "M": "Missing",
        "R": "Replacing",
        "U": "Unnecessary"
    }
    for p_code, p_desc in punctuation_types.items():
        codes.append({
            "code": f"#{p_code}P",
            "category": "Punctuation",
            "description": f"Punctuation {p_desc}"
        })

    # 3. Countability errors (C + word class)
    # "CN countability of Noun, CQ wrong Quantifier..., CD wrong Determiner..."
    countability = {
        "CN": "Countability of Noun error",
        "CQ": "Wrong Quantifier because of noun countability",
        "CD": "Wrong Determiner because of noun countability"
    }
    for code, desc in countability.items():
        codes.append({
            "code": f"#{code}",
            "category": "Countability",
            "description": desc
        })

    # 4. False Friend errors (FF + word class)
    # "All false friend errors are tagged with FF... + word class code"
    for w_code, w_desc in word_classes.items():
        codes.append({
            "code": f"#FF{w_code}",
            "category": "False Friend",
            "description": f"False Friend involving a {w_desc}"
        })

    # 5. Agreement errors (AG + word class)
    # "AGA... AGD... AGN... AGV"
    agreement = {
        "AGA": "Anaphoric (pronoun) agreement error",
        "AGD": "Determiner agreement error",
        "AGN": "Noun agreement error",
        "AGV": "Verb agreement error"
    }
    for code, desc in agreement.items():
        codes.append({
            "code": f"#{code}",
            "category": "Agreement",
            "description": desc
        })

    # 6. Additional/Specific Codes
    # "AS, CE, CL, ID, IN, IV, L, S, SA, SX, TV, W, X"
    misc = {
        "AS": "Incorrect Argument Structure",
        "CE": "Complex Error",
        "CL": "Collocation error",
        "ID": "Idiom error",
        "IN": "Incorrect formation of Noun plural",
        "IV": "Incorrect Verb inflection",
        "L": "Inappropriate register (Label)",
        "S": "Spelling error",
        "SA": "American Spelling",
        "SX": "Spelling confusion error",
        "TV": "Wrong Tense of Verb",
        "W": "Incorrect Word order",
        "X": "Incorrect formation of negative"
    }
    for code, desc in misc.items():
        codes.append({
            "code": f"#{code}",
            "category": "Miscellaneous",
            "description": desc
        })

    # 7. Single Letter Codes
    # "The codes M, R, and U can occur alone where no more specific information can be given."
    single_codes = {
        "M": "Something Missing (General)",
        "R": "Replace (General)",
        "U": "Unnecessary (General)"
    }
    for code, desc in single_codes.items():
        codes.append({
            "code": f"#{code}",
            "category": "General - Single",
            "description": desc
        })

    # Output
    output = {
        "source": "Algorithmic Generation based on Cambridge Learner Corpus rules (Nicholls, 2003)",
        "count": len(codes),
        "codes": codes
    }
    
    with open('data/firecrawl_errors.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Generated {len(codes)} Cambridge Error Codes.")

if __name__ == "__main__":
    generate_cambridge_codes()
