#!/usr/bin/env python3
"""Quick view of marked turns from a session"""
import json, sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python view_marked.py <session.json>")
    sys.exit(1)

session_file = Path(sys.argv[1])
if not session_file.exists():
    print(f"Error: File not found: {session_file}")
    sys.exit(1)

with open(session_file) as f:
    session = json.load(f)

marked = [t for t in session.get('turns', []) if t.get('marked')]
if not marked:
    print("\n❌ No marked turns in this session\n")
    sys.exit(0)

print(f"\n{'='*70}")
print(f"⭐ MARKED TURNS - {session.get('speaker', 'Unknown')}")
print(f"Session: {session.get('start_time', 'Unknown')[:10]}")
print(f"{'='*70}\n")

for i, t in enumerate(marked, 1):
    mark_type = t.get('mark_type', 'unknown').upper()
    emoji = {'FRONT': '🗣️', 'BACK': '📖', 'ALL': '✏️'}.get(mark_type, '📌')
    print(f"{i}. {emoji} [{mark_type}] Turn #{t['turn_order']}")
    print(f"   {t['transcript']}\n")

print(f"{'='*70}\nTotal marked: {len(marked)}\n{'='*70}\n")
