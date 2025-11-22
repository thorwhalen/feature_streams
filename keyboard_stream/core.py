"""
Core implementation for keyboard streaming with MIDI note mapping.
"""

import sys
import os
from typing import Iterator, Dict, Any, Optional
from dataclasses import dataclass, field
from queue import Queue, Empty
from pynput import keyboard
import time

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp

# Default key-to-MIDI-note mapping (C major scale on home row)
DEFAULT_KEY_MAPPING = {
    'a': 60,  # C4 (Middle C)
    's': 62,  # D4
    'd': 64,  # E4
    'f': 65,  # F4
    'g': 67,  # G4
    'h': 69,  # A4
    'j': 71,  # B4
    'k': 72,  # C5
    # Number row for chromatic notes
    '1': 60, '2': 61, '3': 62, '4': 63, '5': 64, '6': 65,
    '7': 66, '8': 67, '9': 68, '0': 69,
}


@dataclass
class KeyboardConfig:
    """Configuration for keyboard stream."""
    key_to_note: Dict[str, int] = field(default_factory=lambda: DEFAULT_KEY_MAPPING.copy())
    enable_velocity: bool = True
    velocity_range: tuple = (64, 127)  # (min, max) MIDI velocity


class KeyboardStreamState:
    """Maintains state for keyboard streaming."""

    def __init__(self, config: KeyboardConfig):
        self.config = config
        self.event_queue = Queue()
        self.pressed_keys = set()  # Track currently pressed keys
        self.active_modifiers = set()
        self.last_press_time = {}  # Track timing for velocity estimation

    def _get_key_char(self, key) -> Optional[str]:
        """Convert pynput key to character string."""
        try:
            # Regular character keys
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
        except AttributeError:
            pass

        # Special keys
        if isinstance(key, keyboard.Key):
            return key.name

        return None

    def _is_modifier(self, key_char: str) -> bool:
        """Check if key is a modifier."""
        modifiers = {'shift', 'ctrl', 'alt', 'cmd', 'ctrl_l', 'ctrl_r',
                     'shift_l', 'shift_r', 'alt_l', 'alt_r', 'cmd_l', 'cmd_r'}
        return key_char in modifiers

    def _calculate_velocity(self, key_char: str) -> int:
        """
        Estimate velocity based on typing speed.

        Args:
            key_char: Key character

        Returns:
            int: MIDI velocity (0-127)
        """
        if not self.config.enable_velocity:
            return 100  # Default velocity

        current_time = time.time()

        # Calculate velocity based on time since last key press
        if self.last_press_time:
            last_time = max(self.last_press_time.values())
            interval = current_time - last_time

            # Faster typing = higher velocity
            # interval < 0.1s = high velocity, > 0.5s = low velocity
            if interval < 0.1:
                velocity = self.config.velocity_range[1]
            elif interval > 0.5:
                velocity = self.config.velocity_range[0]
            else:
                # Linear interpolation
                t = (interval - 0.1) / 0.4
                velocity = int(self.config.velocity_range[1] -
                              t * (self.config.velocity_range[1] - self.config.velocity_range[0]))
        else:
            velocity = (self.config.velocity_range[0] + self.config.velocity_range[1]) // 2

        self.last_press_time[key_char] = current_time
        return velocity

    def _get_octave_shift(self) -> int:
        """Calculate octave shift based on active modifiers."""
        if 'shift' in self.active_modifiers or 'shift_l' in self.active_modifiers or 'shift_r' in self.active_modifiers:
            return 12  # One octave up
        elif 'ctrl' in self.active_modifiers or 'ctrl_l' in self.active_modifiers or 'ctrl_r' in self.active_modifiers:
            return -12  # One octave down
        return 0

    def on_press(self, key):
        """Callback for key press events."""
        key_char = self._get_key_char(key)
        if not key_char:
            return

        # Track modifiers
        if self._is_modifier(key_char):
            self.active_modifiers.add(key_char)

        # Avoid duplicate press events
        if key_char in self.pressed_keys:
            return

        self.pressed_keys.add(key_char)

        # Get MIDI note if mapped
        midi_note = self.config.key_to_note.get(key_char)
        if midi_note is not None:
            octave_shift = self._get_octave_shift()
            midi_note += octave_shift
            # Clamp to valid MIDI range
            midi_note = max(0, min(127, midi_note))

        velocity = self._calculate_velocity(key_char) if midi_note else 0

        event = {
            'timestamp': timestamp(),
            'key': key_char,
            'event_type': 'press',
            'midi_note': midi_note,
            'midi_velocity': velocity,
            'is_modifier': self._is_modifier(key_char),
            'active_modifiers': list(self.active_modifiers),
            'octave_shift': self._get_octave_shift() // 12,  # Convert to octave count
        }

        self.event_queue.put(event)

    def on_release(self, key):
        """Callback for key release events."""
        key_char = self._get_key_char(key)
        if not key_char:
            return

        # Remove from pressed keys
        self.pressed_keys.discard(key_char)

        # Update modifiers
        if self._is_modifier(key_char):
            self.active_modifiers.discard(key_char)

        # Get MIDI note if mapped
        midi_note = self.config.key_to_note.get(key_char)
        if midi_note is not None:
            octave_shift = self._get_octave_shift()
            midi_note += octave_shift
            midi_note = max(0, min(127, midi_note))

        event = {
            'timestamp': timestamp(),
            'key': key_char,
            'event_type': 'release',
            'midi_note': midi_note,
            'midi_velocity': 0,  # Release has zero velocity
            'is_modifier': self._is_modifier(key_char),
            'active_modifiers': list(self.active_modifiers),
            'octave_shift': self._get_octave_shift() // 12,
        }

        self.event_queue.put(event)


def keyboard_stream(config: Optional[KeyboardConfig] = None) -> Iterator[Dict[str, Any]]:
    """
    Generate stream of keyboard events.

    Args:
        config: Optional configuration (uses defaults if None)

    Yields:
        Dict: Stream items with keyboard events

    Example:
        >>> for event in keyboard_stream():
        ...     if event['event_type'] == 'press' and event['midi_note']:
        ...         print(f"Note {event['midi_note']} pressed")
    """
    if config is None:
        config = KeyboardConfig()

    state = KeyboardStreamState(config)

    # Start keyboard listener
    listener = keyboard.Listener(
        on_press=state.on_press,
        on_release=state.on_release
    )
    listener.start()

    try:
        while True:
            # Get events from queue (blocking with timeout)
            try:
                event = state.event_queue.get(timeout=0.1)
                yield event
            except Empty:
                continue
    finally:
        listener.stop()
