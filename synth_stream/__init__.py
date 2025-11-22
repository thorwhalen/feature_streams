"""
SYNTH_STREAM (dict_to_audio)

Consume a stream of control dictionaries and generate real-time audio output
using a synthesis engine. Provides low-latency, parameter-driven sound generation.
"""

from .core import (
    synth_stream_consumer,
    SynthConfig,
    Waveform,
)

__version__ = "0.1.0"
__all__ = ["synth_stream_consumer", "SynthConfig", "Waveform"]
