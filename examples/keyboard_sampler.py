#!/usr/bin/env python3
"""
Keyboard Sampler - Multi-voice keyboard synthesizer with different waveforms.

Dependencies:
    pip install pynput numpy sounddevice

Usage:
    python examples/keyboard_sampler.py

Controls:
    - Home row (A-K): Play notes (C major scale)
    - Number row (1-9): Play chromatic notes
    - Shift: Octave up
    - Ctrl: Octave down
    - Ctrl+C: Exit
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyboard_stream import keyboard_stream
from midi_out_stream import midi_out_stream_consumer, MIDIConfig


def keyboard_to_midi_sampler():
    """
    Convert keyboard to MIDI with polyphonic support.
    """
    print("🎹 Keyboard Sampler")
    print("   Home row (A-K): C major scale")
    print("   Number row: Chromatic")
    print("   Shift: Octave up")
    print("   Ctrl: Octave down")
    print("   Press Ctrl+C to exit\n")

    for event in keyboard_stream():
        if event['midi_note'] is not None:
            # Note on when pressed
            if event['event_type'] == 'press':
                yield {
                    'event_type': 'note',
                    'midi_note': event['midi_note'],
                    'velocity': event['midi_velocity'],
                    'channel': 0
                }
            # Note off when released
            elif event['event_type'] == 'release':
                yield {
                    'event_type': 'note',
                    'midi_note': event['midi_note'],
                    'velocity': 0,
                    'channel': 0
                }


if __name__ == "__main__":
    try:
        # Try to create virtual MIDI port
        config = MIDIConfig(create_virtual_port=True, virtual_port_name="Keyboard Sampler")
        print("Created virtual MIDI port: 'Keyboard Sampler'")
        print("Connect this to your favorite synthesizer!\n")

        midi_out_stream_consumer(keyboard_to_midi_sampler(), config)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
