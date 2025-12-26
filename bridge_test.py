from typing import Any
from pydantic import ValidationError
from analyzers.schemas import LanguageFeedback, OfficialCategory, LinguisticSubcategory

# 1. The "Dump" from the TheGuru (Simulated based on UNIVERSAL_GURU_PROMPT.txt)
# This is what the LLM currently thinks it should output
the_guru_dump = {
    "corrections": [
        {
            "wrong": "I have went to the store",
            "right": "I went to the store",
            "explanation": "Simple past is required for a specific time in the past (yesterday)."
        }
    ]
}

# 2. The "Bridge" logic (Simulated from semantic_server.py / llm_gateway.py)
print("🌉 ATTEMPTING TO VALIDATE DATA...")

def bridge_to_petty_dantic(raw_data):
    validated_items = []
    # Note: The prompt outputs 'corrections', but the schema expects 'LanguageFeedback' fields
    items_to_validate = raw_data.get("corrections", [])
    
    for item in items_to_validate:
        print(f"\n👉 Processing item: {item}")
        try:
            # Map the LLM fields to Schema fields (This is the 'Bridge')
            # Explicit instantiation to satisfy type checker and match schema field names
            clean_item = LanguageFeedback(
                category=OfficialCategory.GRAMMAR_ERR,
                subcategory=LinguisticSubcategory.SYNTAX,
                specificPhenomenon="Verb Tense",
                suggestedCorrection=item.get("right", ""),
                explanation=item.get("explanation", ""),
                detectedTrigger=item.get("wrong", ""),
                unstructuredInsight=f"Teacher corrected '{item.get('wrong')}' to '{item.get('right')}'"
            )
            validated_items.append(clean_item.model_dump())
            print("✅ BRIDGE CROSSED: Item Validated.")
            
        except ValidationError as e:
            print(f"❌ VALIDATION FAILED: Schema rejected the item.")
            print(f"   Errors: {e.json()}")
        except Exception as e:
            print(f"💥 BRIDGE EXPLODED: {e}")
            
    return validated_items

results = bridge_to_petty_dantic(the_guru_dump)
print(f"\n📊 Final Validated Count: {len(results)}/1")
