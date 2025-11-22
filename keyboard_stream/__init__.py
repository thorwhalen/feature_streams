"""
KEYBOARD_STREAM (key_to_note)

Capture keyboard key presses and releases, converting them into a structured,
time-stamped stream with optional MIDI note mapping for musical control.
"""

from .core import (
    keyboard_stream,
    KeyboardConfig,
    DEFAULT_KEY_MAPPING,
)

__version__ = "0.1.0"
__all__ = ["keyboard_stream", "KeyboardConfig", "DEFAULT_KEY_MAPPING"]
