import json
import csv
import os
import re
from pathlib import Path

def merge():
    base_dir = Path("/Users/safeSpacesBro/AssemblyAIv2")
    data_dir = base_dir / "data"
    hub_dir = Path("/Users/safeSpacesBro/gitenglishhub")
    
    # 1. Load existing primary error phenomena
    primary_json_path = data_dir / "error_phenomena.json"
    with open(primary_json_path, 'r', encoding='utf-8') as f:
        phenomena = json.load(f)
    print(f"Loaded {len(phenomena)} primary phenomena.")
    
    existing_ids = {p.get("phenomenon_id") for p in phenomena if p.get("phenomenon_id")}
    
    # 2. Add patterns from parsed_error_patterns.csv
    csv_path = hub_dir / "ErrorCorp" / "parsed_error_patterns.csv"
    csv_added = 0
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic cleaning
                phen_id = row.get("phenomenon_id") or row.get("itemName")
                if phen_id in existing_ids:
                    continue
                
                # Standardize fields
                new_phen = {
                    "phenomenon_id": f"err_csv_{csv_added:04d}",
                    "itemName": row.get("itemName", "Unknown"),
                    "publicCategory": row.get("publicCategory", "Grammar"),
                    "subcategory": row.get("subcategory", "General"),
                    "triggerPattern": row.get("triggerPattern", ""),
                    "exampleErrors": row.get("exampleErrors", ""),
                    "exampleCorrections": row.get("exampleCorrections", ""),
                    "explanation": row.get("explanation", ""),
                    "cefrLevel": row.get("cefrLevel", ""),
                    "severity": row.get("severity", "medium"),
                    "source": row.get("source", "csv_import"),
                    "confidenceScore": 0.75
                }
                
                if new_phen["triggerPattern"]:
                    phenomena.append(new_phen)
                    existing_ids.add(new_phen["phenomenon_id"])
                    csv_added += 1
    print(f"Added {csv_added} phenomena from CSV.")

    # 3. Add Discourse Connectors (DCL)
    dcl_json_path = hub_dir / "data" / "phenomena" / "dcl_phenomena.json"
    dcl_added = 0
    if dcl_json_path.exists():
        with open(dcl_json_path, 'r', encoding='utf-8') as f:
            dcl_data = json.load(f)
            for item in dcl_data:
                p_id = item.get("phenomenon_id")
                if p_id in existing_ids:
                    continue
                
                item_name = item.get("item_name", "")
                if not item_name:
                    continue
                    
                # Create a regex pattern for the discourse connector
                # Simple word-boundary pattern
                # Note: item_name might contain multi-word units
                escaped = re.escape(item_name)
                pattern = fr"\b{escaped}\b"
                
                new_phen = {
                    "phenomenon_id": p_id or f"disc_dcl_{dcl_added:04d}",
                    "itemName": item_name,
                    "publicCategory": "Discourse",
                    "subcategory": item.get("sub_category", "Connector"),
                    "triggerPattern": pattern,
                    "explanation": item.get("description", ""),
                    "cefrLevel": item.get("cefr_level", ""),
                    "source": "DCL",
                    "confidenceScore": 0.8
                }
                
                phenomena.append(new_phen)
                existing_ids.add(new_phen["phenomenon_id"])
                dcl_added += 1
    print(f"Added {dcl_added} phenomena from DCL.")

    # 4. Save the unified database
    output_path = data_dir / "unified_phenomena.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(phenomena, f, indent=2)
    
    print(f"Final count: {len(phenomena)} items saved to {output_path}")

if __name__ == "__main__":
    merge()
