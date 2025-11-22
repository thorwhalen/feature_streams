"""
TTS_STREAM (dict_to_speech)

Consume a stream of text dictionaries and generate real-time text-to-speech audio output.
Supports dynamic parameter control (speed, pitch, voice selection).
"""

from .core import (
    tts_stream_consumer,
    TTSConfig,
    list_voices,
)

__version__ = "0.1.0"
__all__ = ["tts_stream_consumer", "TTSConfig", "list_voices"]
