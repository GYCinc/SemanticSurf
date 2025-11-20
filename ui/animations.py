"""ASCII Surfer Animation System"""
from datetime import timedelta

class SurferAnimation:
    SURFER_FRAMES = [
        """
        [bold yellow]      ,___,
        [bold yellow]      [__]
        [bold yellow]     /|  |\
        [bold yellow]    / |  | \
        [bold blue]   /~~~~~~~~~\
        [bold blue]  /~~~~~~~~~~~\
        [bold blue] /~~~~~~~~~~~~~\
        """,
        """
        [bold yellow]      ,___,
        [bold yellow]      [__]
        [bold yellow]     /|  |\
        [bold yellow]    / |  | \
        [bold blue]  /~~~~~~~~~~~\
        [bold blue] /~~~~~~~~~~~~~\
        [bold blue]/~~~~~~~~~~~~~~~\
        """,
        """
        [bold yellow]      ,___,
        [bold yellow]      [__]
        [bold yellow]     /|  |\
        [bold yellow]    / |  | \
        [bold blue] /~~~~~~~~~~~~~\
        [bold blue]/~~~~~~~~~~~~~~~\
        [bold blue]~~~~~~~~~~~~~~~~~\
        """,
        """
        [bold yellow]      ,___,
        [bold yellow]      [__]
        [bold yellow]     /|  |\
        [bold yellow]    / |  | \
        [bold blue]/~~~~~~~~~~~~~~~\
        [bold blue]~~~~~~~~~~~~~~~~~\
        [bold blue]~~~~~~~~~~~~~~~~~~~\
        """,
    ]

    def __init__(self):
        self.current_frame = 0

    def get_frame(self):
        frame = self.SURFER_FRAMES[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.SURFER_FRAMES)
        return frame

class SunAnimation:
    SUN_CHARS = ["☀️", "🌤️", "⛅️", "🌥️", "☁️", " ", " ", " ", " ", " "]
    SUN_COLORS = ["bold yellow", "yellow", "bright_yellow", "white", "dim", "dim", "dim", "dim", "dim", "dim"]
    TOTAL_DURATION_MINUTES = 50

    def get_frame(self, elapsed_time: timedelta):
        total_seconds = elapsed_time.total_seconds()
        percentage = min(total_seconds / (self.TOTAL_DURATION_MINUTES * 60), 1.0)
        
        index = int(percentage * (len(self.SUN_CHARS) - 1))
        
        sun_char = self.SUN_CHARS[index]
        sun_color = self.SUN_COLORS[index]
        
        return "[" + sun_color + "]" + sun_char + "[/]"
