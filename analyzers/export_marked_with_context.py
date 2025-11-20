#!/usr/bin/env python3
"""
Export marked turns with context for LLM analysis

This script reads a session JSON file and exports all marked turns
with 3 turns of context before and after each marked turn.

Usage:
    python export_marked_with_context.py sessions/session_2025-10-31_15-35-14.json
"""

import json
import sys
from pathlib import Path


def get_context_for_marked_turns(session_data, context_size=3):
    """
    Extract marked turns with surrounding context.
    Handles overlapping contexts intelligently.
    """
    turns = session_data.get('turns', [])
    marked_turns = [t for t in turns if t.get('marked', False)]
    
    if not marked_turns:
        print("No marked turns found in this session.")
        return []
    
    results = []
    
    for marked_turn in marked_turns:
        turn_order = marked_turn['turn_order']
        
        # Get context range
        start_idx = max(0, turn_order - context_size)
        end_idx = min(len(turns), turn_order + context_size + 1)
        
        # Extract context turns
        context_turns = []
        for i in range(start_idx, end_idx):
            turn = next((t for t in turns if t['turn_order'] == i), None)
            if turn:
                context_turns.append({
                    'turn_order': turn['turn_order'],
                    'transcript': turn['transcript'],
                    'is_marked': turn['turn_order'] == turn_order,
                    'mark_type': turn.get('mark_type') if turn['turn_order'] == turn_order else None
                })
        
        results.append({
            'marked_turn_order': turn_order,
            'mark_type': marked_turn.get('mark_type'),
            'mark_timestamp': marked_turn.get('mark_timestamp'),
            'context': context_turns,
            'context_text': '\n'.join([
                f"{'>>> ' if t['is_marked'] else '    '}{t['transcript']}"
                for t in context_turns
            ])
        })
    
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_marked_with_context.py <session_file.json>")
        print("\nExample:")
        print("  python export_marked_with_context.py sessions/session_2025-10-31_15-35-14.json")
        sys.exit(1)
    
    session_file = Path(sys.argv[1])
    
    if not session_file.exists():
        print(f"Error: File not found: {session_file}")
        sys.exit(1)
    
    # Load session
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    print(f"\n📄 Session: {session_data.get('session_id', 'Unknown')}")
    print(f"🎤 Speaker: {session_data.get('speaker', 'Unknown')}")
    print(f"📅 Date: {session_data.get('start_time', 'Unknown')}")
    print(f"📊 Total turns: {session_data.get('total_turns', 0)}")
    
    # Extract marked turns with context
    marked_with_context = get_context_for_marked_turns(session_data)
    
    if not marked_with_context:
        sys.exit(0)
    
    print(f"\n✓ Found {len(marked_with_context)} marked turns\n")
    
    # Display results
    for i, item in enumerate(marked_with_context, 1):
        print(f"{'='*70}")
        print(f"Marked Turn #{i} (Turn Order: {item['marked_turn_order']})")
        print(f"Mark Type: {item['mark_type']}")
        print(f"{'='*70}")
        print(item['context_text'])
        print()
    
    # Save to file
    output_file = session_file.parent / f"{session_file.stem}_marked_export.json"
    with open(output_file, 'w') as f:
        json.dump({
            'session_info': {
                'session_id': session_data.get('session_id'),
                'speaker': session_data.get('speaker'),
                'start_time': session_data.get('start_time'),
                'total_turns': session_data.get('total_turns')
            },
            'marked_turns': marked_with_context
        }, f, indent=2)
    
    print(f"💾 Exported to: {output_file}")
    print(f"\n✅ Done! You can now feed this to an LLM for analysis.")


if __name__ == '__main__':
    main()