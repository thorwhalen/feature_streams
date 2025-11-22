"""
MIDI_OUT_STREAM (dict_to_midi)

Consume a stream of musical control dictionaries and output MIDI messages to
hardware/software synthesizers, DAWs, or virtual MIDI ports.
"""

from .core import (
    midi_out_stream_consumer,
    MIDIConfig,
    list_midi_ports,
)

__version__ = "0.1.0"
__all__ = ["midi_out_stream_consumer", "MIDIConfig", "list_midi_ports"]
