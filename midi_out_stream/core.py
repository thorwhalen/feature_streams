"""
Core implementation for MIDI output stream consumer.
"""

import sys
import os
from typing import Iterator, Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from threading import Thread, Lock
import time
import warnings

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp

# Import MIDI dependencies
try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    warnings.warn("mido not installed. Install with: pip install mido python-rtmidi")


@dataclass
class MIDIConfig:
    """Configuration for MIDI output."""
    port_name: Optional[str] = None  # None = default output port
    create_virtual_port: bool = False
    virtual_port_name: str = "feature_streams_midi_out"
    default_channel: int = 0  # 0-15 (MIDI channels 1-16)
    auto_note_off_delay: float = 0.5  # Auto note-off for notes with duration


def list_midi_ports() -> List[str]:
    """
    List available MIDI output ports.

    Returns:
        List of MIDI port names
    """
    if not MIDO_AVAILABLE:
        return []

    return mido.get_output_names()


class MIDIOutputEngine:
    """MIDI output engine."""

    def __init__(self, config: MIDIConfig):
        if not MIDO_AVAILABLE:
            raise RuntimeError("mido not installed")

        self.config = config
        self.lock = Lock()

        # Track active notes (for cleanup)
        self.active_notes: Set[tuple] = set()  # (channel, note)

        # Scheduled note-offs
        self.scheduled_note_offs = []  # [(time, channel, note), ...]
        self.note_off_thread = None
        self.stop_note_off_thread = False

        # Open MIDI port
        if config.create_virtual_port:
            try:
                self.port = mido.open_output(config.virtual_port_name, virtual=True)
            except:
                warnings.warn("Virtual ports not supported on this platform, using default port")
                self.port = mido.open_output()
        elif config.port_name:
            self.port = mido.open_output(config.port_name)
        else:
            # Use default port
            ports = list_midi_ports()
            if ports:
                self.port = mido.open_output(ports[0])
            else:
                # No ports available, create virtual as fallback
                try:
                    self.port = mido.open_output('feature_streams_default', virtual=True)
                except:
                    raise RuntimeError("No MIDI ports available")

        # Start note-off scheduler thread
        self.note_off_thread = Thread(target=self._note_off_scheduler, daemon=True)
        self.note_off_thread.start()

    def _note_off_scheduler(self):
        """Background thread to handle scheduled note-offs."""
        while not self.stop_note_off_thread:
            current_time = time.time()

            with self.lock:
                # Find notes to turn off
                to_remove = []
                for i, (off_time, channel, note) in enumerate(self.scheduled_note_offs):
                    if current_time >= off_time:
                        self._send_note_off(channel, note)
                        to_remove.append(i)

                # Remove processed note-offs
                for i in reversed(to_remove):
                    del self.scheduled_note_offs[i]

            time.sleep(0.01)  # 10ms resolution

    def _send_note_on(self, channel: int, note: int, velocity: int):
        """Send MIDI note on message."""
        msg = mido.Message('note_on', channel=channel, note=note, velocity=velocity)
        self.port.send(msg)
        self.active_notes.add((channel, note))

    def _send_note_off(self, channel: int, note: int):
        """Send MIDI note off message."""
        msg = mido.Message('note_off', channel=channel, note=note, velocity=0)
        self.port.send(msg)
        self.active_notes.discard((channel, note))

    def _send_control_change(self, channel: int, control: int, value: int):
        """Send MIDI control change message."""
        msg = mido.Message('control_change', channel=channel, control=control, value=value)
        self.port.send(msg)

    def _send_pitch_bend(self, channel: int, pitch: int):
        """Send MIDI pitch bend message."""
        msg = mido.Message('pitchwheel', channel=channel, pitch=pitch)
        self.port.send(msg)

    def _send_program_change(self, channel: int, program: int):
        """Send MIDI program change message."""
        msg = mido.Message('program_change', channel=channel, program=program)
        self.port.send(msg)

    def process_control_dict(self, control_dict: Dict[str, Any]):
        """
        Process control dictionary and send MIDI messages.

        Args:
            control_dict: Control parameters
        """
        with self.lock:
            event_type = control_dict.get('event_type', 'note')
            channel = control_dict.get('channel', self.config.default_channel)

            # Ensure channel is in valid range (0-15)
            channel = max(0, min(15, channel))

            if event_type == 'note':
                # Note event
                midi_note = control_dict.get('midi_note')
                velocity = control_dict.get('velocity', 100)
                duration = control_dict.get('duration')

                if midi_note is not None:
                    # Clamp to MIDI range
                    midi_note = max(0, min(127, midi_note))
                    velocity = max(0, min(127, velocity))

                    if velocity > 0:
                        # Note on
                        self._send_note_on(channel, midi_note, velocity)

                        # Schedule note off if duration specified
                        if duration is not None and duration > 0:
                            off_time = time.time() + duration
                            self.scheduled_note_offs.append((off_time, channel, midi_note))

                    else:
                        # Note off (velocity = 0)
                        self._send_note_off(channel, midi_note)

            elif event_type == 'cc' or event_type == 'control_change':
                # Control change
                cc_number = control_dict.get('cc_number', 0)
                cc_value = control_dict.get('cc_value', 0)

                cc_number = max(0, min(127, cc_number))
                cc_value = max(0, min(127, cc_value))

                self._send_control_change(channel, cc_number, cc_value)

            elif event_type == 'pitch_bend':
                # Pitch bend
                pitch_bend = control_dict.get('pitch_bend', 0)
                pitch_bend = max(-8192, min(8191, pitch_bend))
                self._send_pitch_bend(channel, pitch_bend)

            elif event_type == 'program_change':
                # Program change
                program = control_dict.get('program', 0)
                program = max(0, min(127, program))
                self._send_program_change(channel, program)

    def all_notes_off(self):
        """Turn off all active notes."""
        with self.lock:
            for channel, note in list(self.active_notes):
                self._send_note_off(channel, note)
            self.active_notes.clear()
            self.scheduled_note_offs.clear()

    def close(self):
        """Close MIDI port and cleanup."""
        self.stop_note_off_thread = True
        if self.note_off_thread:
            self.note_off_thread.join(timeout=1.0)

        self.all_notes_off()
        self.port.close()


def midi_out_stream_consumer(
    control_stream: Iterator[Dict[str, Any]],
    config: Optional[MIDIConfig] = None
):
    """
    Consume control stream and send MIDI messages.

    Args:
        control_stream: Iterator yielding control dictionaries
        config: Optional MIDI configuration

    Example:
        >>> def control_gen():
        ...     # Play C major scale
        ...     for note in [60, 62, 64, 65, 67, 69, 71, 72]:
        ...         yield {
        ...             'event_type': 'note',
        ...             'midi_note': note,
        ...             'velocity': 100,
        ...             'duration': 0.5,
        ...             'channel': 0
        ...         }
        ...         time.sleep(0.5)
        >>>
        >>> midi_out_stream_consumer(control_gen())
    """
    if config is None:
        config = MIDIConfig()

    engine = MIDIOutputEngine(config)

    try:
        for control_dict in control_stream:
            engine.process_control_dict(control_dict)
    finally:
        engine.close()
