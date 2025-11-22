#!/usr/bin/env python3
"""
Voice Theremin - Control synthesizer with your voice pitch and loudness.

Dependencies:
    pip install numpy sounddevice aubio

Usage:
    python examples/voice_theremin.py

How it works:
    - Sing/hum into your microphone
    - Your pitch controls the synthesizer frequency
    - Your loudness controls the volume
    - Spectral centroid controls filter brightness

Controls:
    - Ctrl+C: Exit
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_input_stream import audio_input_stream, list_audio_devices
from synth_stream import synth_stream_consumer
import math


def voice_to_synth():
    """
    Map voice features to synthesizer parameters.
    """
    # List audio devices
    devices = list_audio_devices()
    if not devices:
        print("❌ No audio input devices found!")
        return

    print("🎤 Voice Theremin")
    print(f"   Using: {devices[0]['name']}")
    print("   Sing or hum to control the synth!")
    print("   Pitch → Frequency")
    print("   Loudness → Volume")
    print("   Press Ctrl+C to exit\n")

    for features in audio_input_stream():
        if features['is_voiced']:
            # Use detected pitch
            pitch_hz = features['pitch_hz']

            # Use loudness for amplitude
            amplitude = features['loudness_norm']

            # Use spectral centroid for waveform selection
            if features['spectral_centroid_norm'] > 0.5:
                waveform = 'saw'  # Bright sound
            else:
                waveform = 'sine'  # Dark sound

            yield {
                'pitch_hz': pitch_hz,
                'amplitude': amplitude * 0.8,
                'waveform_type': waveform
            }
        else:
            # Silence when not voiced
            yield {
                'pitch_hz': 440.0,
                'amplitude': 0.0,
                'waveform_type': 'sine'
            }


if __name__ == "__main__":
    try:
        synth_stream_consumer(voice_to_synth())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
