#!/usr/bin/env python3
"""
Theremin - Classic theremin using trackpad position to control pitch and volume.

Dependencies:
    pip install pynput numpy sounddevice

Usage:
    python examples/theremin.py

Controls:
    - X position (left/right): Pitch (200-800 Hz)
    - Y position (up/down): Volume
    - Left click: Toggle square wave
    - Right click: Enable vibrato
    - Ctrl+C: Exit
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trackpad_stream import trackpad_stream
from synth_stream import synth_stream_consumer
from transforms import linear_map
import math


def theremin():
    """
    Map trackpad to theremin-style synthesizer.
    """
    print("🎵 Theremin - Move your mouse/trackpad to play!")
    print("   X (left/right) = Pitch")
    print("   Y (up/down) = Volume")
    print("   Left click = Square wave")
    print("   Right click = Vibrato")
    print("   Press Ctrl+C to exit\n")

    vibrato_phase = 0.0

    for event in trackpad_stream():
        # Map X to pitch (200-800 Hz)
        pitch_hz = linear_map(event['x_norm'], (0, 1), (200, 800))

        # Map Y to volume (inverted: top = loud, bottom = quiet)
        amplitude = 1.0 - event['y_norm']

        # Waveform selection
        waveform = 'square' if event['left_click'] else 'sine'

        # Add vibrato if right click
        if event['right_click']:
            vibrato_phase += 0.1
            vibrato = 5 * math.sin(vibrato_phase)  # 5 Hz vibrato
            pitch_hz += vibrato

        yield {
            'pitch_hz': pitch_hz,
            'amplitude': amplitude * 0.7,  # Scale down to prevent clipping
            'waveform_type': waveform
        }


if __name__ == "__main__":
    try:
        synth_stream_consumer(theremin())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
