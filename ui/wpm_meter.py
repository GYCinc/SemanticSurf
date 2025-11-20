"""Real-time WPM Meter Display"""
from rich.text import Text
from rich.panel import Panel

class WPMMeter:
    def __init__(self):
        self.current_wpm = 0
        
    def get_wpm_display(self, wpm):
        if wpm is None:
            return Text("WPM: --", style="dim")
        
        self.current_wpm = wpm
        
        if wpm < 100:
            color = "blue"
            status = "🐢 Slow"
        elif wpm < 140:
            color = "cyan"
            status = "🌊 Normal"
        elif wpm < 180:
            color = "yellow"
            status = "🏄 Fast"
        else:
            color = "red"
            status = "⚡ Rapid"
        
        bar_length = min(int((wpm / 200) * 30), 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        
        text = Text()
        text.append(f"{int(wpm)} WPM ", style=f"bold {color}")
        text.append(f"[{bar}] ", style=color)
        text.append(status, style=f"bold {color}")
        return text
    
    def get_compact_display(self, wpm):
        if wpm is None:
            return Text("-- WPM", style="dim")
        
        if wpm < 100:
            color = "blue"
        elif wpm < 140:
            color = "cyan"
        elif wpm < 180:
            color = "yellow"
        else:
            color = "red"
        
        return Text(f"{int(wpm)} WPM", style=f"bold {color}")
