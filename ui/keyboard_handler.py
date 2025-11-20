"""Keyboard Handler for Terminal UI"""
import sys
import tty
import termios
import threading
from typing import Callable

class KeyboardHandler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.callbacks = {}
        
    def register_callback(self, key: str, callback: Callable):
        self.callbacks[key] = callback
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _listen(self):
        # Check if stdin is a TTY before attempting terminal operations
        if not sys.stdin.isatty():
            print("⚠️  Keyboard input disabled: not running in interactive terminal")
            return
        
        fd = sys.stdin.fileno()
        
        try:
            old_settings = termios.tcgetattr(fd)
        except (termios.error, OSError) as e:
            print(f"⚠️  Keyboard input disabled: {e}")
            return
        
        try:
            tty.setraw(fd)
            while self.running:
                char = sys.stdin.read(1)
                
                if char == '\x1b':
                    char2 = sys.stdin.read(1)
                    if char2 == '[':
                        char3 = sys.stdin.read(1)
                        if char3 == 'A':
                            key = 'up'
                        elif char3 == 'B':
                            key = 'down'
                        else:
                            continue
                    else:
                        continue
                elif char == ' ':
                    key = 'space'
                elif char == '\x03':
                    key = 'ctrl_c'
                elif char == '\r':
                    key = 'enter'
                else:
                    key = char.lower()
                
                if key in self.callbacks:
                    try:
                        self.callbacks[key]()
                    except Exception as e:
                        print(f"Error in callback for key '{key}': {e}")
                
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except (termios.error, OSError):
                pass
