"""
AUDIO_INPUT_STREAM (mic_features)

Capture live microphone/audio input and extract musical features in real-time,
outputting them as a control stream.
"""

from .core import (
    audio_input_stream,
    AudioInputConfig,
    list_audio_devices,
)

__version__ = "0.1.0"
__all__ = ["audio_input_stream", "AudioInputConfig", "list_audio_devices"]
