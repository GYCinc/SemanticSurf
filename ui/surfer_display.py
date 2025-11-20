"""Main Surfer Display - The BALLER Terminal UI"""
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from datetime import datetime, timedelta
import threading
import time

from .animations import SurferAnimation, SunAnimation

class SurferDisplay:
    def __init__(self, speaker_name="Speaker"):
        self.console = Console()
        self.speaker_name = speaker_name
        self.surfer_animation = SurferAnimation()
        self.sun_animation = SunAnimation()
        
        self.transcripts = []
        self.current_wpm = None
        self.session_id = None
        self.is_listening = False
        self.max_visible_lines = 20
        
        self.layout = Layout()
        self.update_lock = threading.Lock()
        self.is_running = False
        self.thread = None
        self.start_time = None

    def start(self):
        self.is_running = True
        self.start_time = datetime.now()
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()

    def _run(self):
        while self.is_running:
            self.draw()
            time.sleep(0.1)

    def draw(self):
        with self.update_lock:
            self.console.clear()
            self.setup_layout()
            self.console.print(self.layout)

    def setup_layout(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=12),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["header"].update(self.render_header())
        self.layout["main"].update(self.render_transcripts())
        self.layout["footer"].update(self.render_footer())

    def render_header(self):
        surfer_frame = self.surfer_animation.get_frame()
        
        elapsed_time = timedelta(seconds=0)
        if self.start_time:
            elapsed_time = datetime.now() - self.start_time
            
        sun_frame = self.sun_animation.get_frame(elapsed_time)

        header_text = Text()
        header_text.append("🌊 SEMANTIC SURFER 🏄\n", style="bold cyan")
        header_text.append(f"Speaker: {self.speaker_name}\n", style="cyan")
        
        if self.session_id:
            header_text.append(f"Session: {self.session_id[:8]}...\n", style="dim cyan")

        if self.current_wpm:
            header_text.append(f"WPM: {self.current_wpm}\n", style="bold yellow")

        return Panel(
            Align.center(
                Text.from_markup(surfer_frame + "\n" + sun_frame, justify="center"),
                vertical="middle"
            ),
            title=header_text,
            border_style="bold blue"
        )

    def render_transcripts(self):
        if not self.transcripts:
            waiting_text = Text()
            waiting_text.append("\n\n", style="")
            waiting_text.append("🎤 Listening for audio...\n\n", style="bold cyan")
            waiting_text.append("Speak now to see your words ride the waves!", style="cyan")
            return Panel(
                Align.center(waiting_text, vertical="middle"),
                title="📝 Transcript",
                border_style="blue",
                padding=(2, 4)
            )
        
        visible_transcripts = self.transcripts[-self.max_visible_lines:]
        
        transcript_text = Text()
        for i, (text, wpm, timestamp) in enumerate(visible_transcripts):
            line_num = len(self.transcripts) - len(visible_transcripts) + i + 1
            transcript_text.append(f"{line_num:3d} │ ", style="dim cyan")
            transcript_text.append(text, style="white")
            
            if wpm:
                transcript_text.append(f" ({wpm} WPM)", style="bold yellow")
            
            transcript_text.append("\n")
        
        return Panel(
            transcript_text,
            title="📝 Transcript",
            border_style="blue",
            padding=(1, 2)
        )

    def render_footer(self):
        controls = Text()
        controls.append("Controls: ", style="bold cyan")
        controls.append("7", style="bold yellow")
        controls.append("=Front ", style="cyan")
        controls.append("8", style="bold yellow")
        controls.append("=All ", style="cyan")
        controls.append("9", style="bold yellow")
        controls.append("=Back ", style="cyan")
        controls.append("5", style="bold yellow")
        controls.append("=Clear ", style="cyan")
        controls.append("Space", style="bold yellow")
        controls.append("=Pause ", style="cyan")
        controls.append("E", style="bold yellow")
        controls.append("=Export", style="cyan")
        
        return Panel(
            controls,
            border_style="cyan"
        )

    def add_transcript(self, text, wpm=None):
        with self.update_lock:
            timestamp = datetime.now()
            self.transcripts.append((text, wpm, timestamp))
            self.current_wpm = wpm

    def set_session_id(self, session_id):
        with self.update_lock:
            self.session_id = session_id
            self.is_listening = True

    def set_listening(self, is_listening):
        with self.update_lock:
            self.is_listening = is_listening

    def show_startup_splash(self):
        pass
