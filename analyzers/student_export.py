#!/usr/bin/env python3
"""
Student-Facing Export System
Converts session analysis into student-friendly formats
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class StudentExporter:
    """Export session data in student-friendly formats"""

    def __init__(self, session_file: Path):
        try:
            with open(session_file, 'r') as f:
                self.session = json.load(f)
        except Exception as e:
            print(f"FATAL: Could not load session file {session_file}: {e}")
            sys.exit(1)

        self.student_name = self.session.get('student_name', 'Student')
        self.student_label = 'Unknown'
        for label, name in self.session.get('speaker_map', {}).items():
            if name == self.student_name:
                self.student_label = label
                break

        # Load analysis if it exists
        analysis_file = session_file.parent / f"{session_file.stem}_analysis.json"
        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                self.analysis = json.load(f)
        else:
            print(f"Warning: Analysis file not found: {analysis_file}")
            self.analysis = None

    def export_markdown(self) -> str:
        """Export as Markdown (works everywhere - copy/paste friendly)"""
        md = []

        # Header
        md.append(f"# 📚 Lesson Summary: {self.student_name}")
        md.append(f"**Date:** {self.session.get('start_time', 'Unknown')[:10]}")
        md.append("")

        # Key Metrics (Student-Only)
        if self.analysis and 'student_metrics' in self.analysis:
            metrics = self.analysis['student_metrics']
            md.append("## 📊 Your Progress (Quantifiable Metrics)")
            md.append("")

            # Speaking Rate
            if 'speaking_rate' in metrics and 'error' not in metrics['speaking_rate']:
                sr = metrics['speaking_rate']
                md.append(f"### 🗣️ Speaking Speed")
                md.append(f"- **Average:** {sr.get('average_wpm', 'N/A')} WPM")
                md.append(f"- **WPM Range:** {sr.get('min_wpm', 'N/A')} (min) - {sr.get('max_wpm', 'N/A')} (max)")
                md.append("")

            # Fluency
            if 'pauses' in metrics and 'message' not in metrics['pauses']:
                p = metrics['pauses']
                md.append(f"### ⏸️ Fluency")
                md.append(f"- **Long Pauses (>1s):** {p.get('long_pauses_gt_1s', 0)}")
                md.append(f"- **Average Pause:** {p.get('average_pause_ms', 0)} ms")
                md.append(f"- **Total Pause Time:** {round(p.get('total_pause_time_ms', 0) / 1000, 1)} seconds")
                md.append("")

            # Vocabulary
            if 'complexity_basic' in metrics and 'error' not in metrics['complexity_basic']:
                c = metrics['complexity_basic']
                md.append(f"### 📚 Vocabulary")
                md.append(f"- **Total Words Spoken:** {c.get('total_words', 0)}")
                md.append(f"- **Unique Words Used:** {c.get('unique_words', 0)}")
                md.append(f"- **Vocabulary Diversity:** {int(c.get('vocabulary_diversity', 0) * 100)}%")
                md.append("")

            # Local AI Analysis (TextBlob)
            if 'advanced_local_analysis' in metrics and 'error' not in metrics['advanced_local_analysis']:
                local_ai = metrics['advanced_local_analysis']
                md.append(f"### 🤖 Free AI Analysis")
                md.append(f"- **Overall Tone:** {local_ai.get('polarity_assessment', 'N/A')}")
                md.append(f"- **Speaking Style:** {local_ai.get('subjectivity_assessment', 'N/A')}")

                top_topics = local_ai.get('top_noun_phrases', {})
                if top_topics:
                    md.append("- **Key Topics You Discussed:**")
                    for topic, count in top_topics.items():
                        md.append(f"  - {topic} ({count} times)")
                md.append("")

        # --- NEW: LM Gateway Analysis ---
        if self.analysis and 'lm_analysis' in self.analysis:
            lm = self.analysis['lm_analysis']
            md.append("## 🤖 deep AI Analysis (LM Gateway)")
            md.append(f"**Your Prompt:** _{lm.get('prompt', 'N/A')}_")
            md.append("")
 
            # This 'response' key is what we saved in lm_gateway.py
            if 'response' in lm:
                # LM Gateway often returns markdown, so we just append it raw
                md.append(lm['response'])
 
            md.append("")
        # --- END NEW ---

        # Marked Moments (Things to Review)
        if self.analysis and 'marked_turns' in self.analysis:
            marked_turns = self.analysis['marked_turns'].get('marked_turns', [])
            if marked_turns:
                md.append("## ⭐ Important Moments to Review")
                md.append("")

                for turn in marked_turns[:15]: # Show up to 15
                    mark_type = turn.get('mark_type', 'review')
                    speaker = turn.get('speaker', 'Unknown')
                    emoji = {'front': '🗣️', 'back': '📖', 'all': '✏️'}.get(mark_type, '📌')
                    md.append(f"### {emoji} {mark_type.title()} ({speaker})")
                    md.append(f"> {turn['transcript']}")
                    md.append("")

        # Full Transcript (Student Only)
        md.append("## 📝 Your Full Transcript")
        md.append("")

        if self.student_label == 'Unknown':
            md.append("_(Could not separate student transcript)_")
        else:
            student_turn_count = 0
            for turn in self.session.get('turns', []):
                if turn.get('speaker') == self.student_label:
                    md.append(f"- {turn['transcript']}")
                    student_turn_count += 1
            if student_turn_count == 0:
                md.append("_(No student speech was detected for this session)_")

        md.append("")
        md.append("---")
        md.append("*Generated by Semantic Server*")

        return '\n'.join(md)

    # --- All your other export functions (export_notion, etc.) ---
    # --- They will all work by calling self.export_markdown() ---

    def export_notion(self) -> str:
        md = self.export_markdown()
        # ... (rest of your notion logic)
        return md # For now, just return markdown

    def export_onenote(self) -> str:
        # ... (your onenote logic)
        return "<html><body>" + self.export_markdown().replace('\n', '<br/>') + "</body></html>"

    def export_all(self, output_dir: Path):
        """Export in all formats"""
        output_dir.mkdir(exist_ok=True)
        base_name = f"student_export_{self.session.get('start_time', 'unknown')[:10]}_{self.student_name}"

        formats = {
            'markdown': ('.md', self.export_markdown()),
            # Add other exporters here as you refine them
        }

        files_created = []
        for format_name, (ext, content) in formats.items():
            file_path = output_dir / f"{base_name}{ext}"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            files_created.append((format_name, file_path))
        return files_created


def main():
    if len(sys.argv) < 2:
        print("Usage: python student_export.py <session_file.json> [format]")
        print("This script is now called automatically by main.py")
        sys.exit(1)

    session_file = Path(sys.argv[1])
    format_type = sys.argv[2] if len(sys.argv) > 2 else 'markdown'

    if not session_file.exists():
        print(f"Error: File not found: {session_file}")
        sys.exit(1)

    exporter = StudentExporter(session_file)

    if format_type == 'all':
        output_dir = session_file.parent / 'student_exports'
        files = exporter.export_all(output_dir)
        print(f"\n✅ Exported {len(files)} formats:")
        for format_name, file_path in files:
            print(f"   {format_name:10} → {file_path}")
    else:
        # Export single format (this is what main.py does)
        content = exporter.export_markdown()
        output_file = session_file.parent / f"student_export_{session_file.stem}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Student Export saved to: {output_file}")


if __name__ == '__main__':
    main()
