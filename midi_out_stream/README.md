# MIDI_OUT_STREAM (dict_to_midi)

Consume a stream of musical control dictionaries and output MIDI messages to hardware/software synthesizers, DAWs, or virtual MIDI ports.

## Features

- MIDI note output (note on/off)
- Control change (CC) messages
- Pitch bend
- Program change (instrument selection)
- Automatic note-off scheduling for timed notes
- Multiple MIDI channel support (1-16)
- Virtual port creation (platform-dependent)
- Active note tracking and cleanup

## Installation

Required dependencies:
```bash
pip install mido python-rtmidi
```

Platform-specific notes:
- **Linux**: May need `libasound2-dev` for ALSA support
- **macOS**: Uses CoreMIDI (built-in)
- **Windows**: Uses Windows MM (built-in)

## Usage

### List MIDI Ports

```python
from midi_out_stream import list_midi_ports

ports = list_midi_ports()
for port in ports:
    print(port)
```

### Basic Note Output

```python
from midi_out_stream import midi_out_stream_consumer
import time

def note_sequence():
    """Play C major scale."""
    scale = [60, 62, 64, 65, 67, 69, 71, 72]  # C4-C5
    for note in scale:
        yield {
            'event_type': 'note',
            'midi_note': note,
            'velocity': 100,
            'duration': 0.5,  # Auto note-off after 0.5s
            'channel': 0
        }
        time.sleep(0.5)

midi_out_stream_consumer(note_sequence())
```

### Custom Port

```python
from midi_out_stream import midi_out_stream_consumer, MIDIConfig

config = MIDIConfig(
    port_name="IAC Driver Bus 1",  # macOS virtual port
    default_channel=0
)

midi_out_stream_consumer(my_control_stream(), config)
```

### Virtual Port

```python
from midi_out_stream import midi_out_stream_consumer, MIDIConfig

config = MIDIConfig(
    create_virtual_port=True,
    virtual_port_name="MyApp MIDI Out"
)

midi_out_stream_consumer(my_control_stream(), config)
```

## Data Contract (Input Stream - Musical Control)

The consumer expects dictionaries with these fields:

```python
{
    'timestamp': float,              # Unix timestamp (optional)
    'event_type': str,               # 'note'|'cc'|'pitch_bend'|'program_change'

    # For note events:
    'midi_note': int,                # MIDI note number (0-127)
    'velocity': int,                 # Note velocity (0-127), 0 = note off
    'duration': float or None,       # Note duration in seconds (None = manual off)

    # For control change:
    'cc_number': int,                # Controller number (0-127)
    'cc_value': int,                 # Controller value (0-127)

    # For pitch bend:
    'pitch_bend': int,               # Pitch bend value (-8192 to 8191)

    # Common:
    'channel': int,                  # MIDI channel (0-15, maps to 1-16)
    'program': int,                  # Program number for program_change (0-127)
}
```

## Example: Keyboard to MIDI

```python
from keyboard_stream import keyboard_stream
from midi_out_stream import midi_out_stream_consumer

def keyboard_to_midi():
    """Convert keyboard events to MIDI notes."""
    for event in keyboard_stream():
        if event['midi_note'] is not None:
            if event['event_type'] == 'press':
                yield {
                    'event_type': 'note',
                    'midi_note': event['midi_note'],
                    'velocity': event['midi_velocity'],
                    'channel': 0
                }
            elif event['event_type'] == 'release':
                yield {
                    'event_type': 'note',
                    'midi_note': event['midi_note'],
                    'velocity': 0,  # Note off
                    'channel': 0
                }

midi_out_stream_consumer(keyboard_to_midi())
```

## Example: Gamepad to MIDI CC

```python
from gamepad_stream import gamepad_stream
from midi_out_stream import midi_out_stream_consumer

def gamepad_to_midi_cc():
    """Map gamepad axes to MIDI control changes."""
    for state in gamepad_stream():
        # Map left stick X to CC 1 (Modulation)
        cc1_value = int((state['left_stick_x'] + 1.0) * 63.5)

        # Map left stick Y to CC 7 (Volume)
        cc7_value = int((state['left_stick_y'] + 1.0) * 63.5)

        yield {'event_type': 'cc', 'cc_number': 1, 'cc_value': cc1_value, 'channel': 0}
        yield {'event_type': 'cc', 'cc_number': 7, 'cc_value': cc7_value, 'channel': 0}

midi_out_stream_consumer(gamepad_to_midi_cc())
```

## MIDI Event Types

### Note Events
- `velocity > 0`: Note on
- `velocity = 0`: Note off
- `duration` specified: Automatic note-off after delay

### Control Change (CC)
Common CC numbers:
- 1: Modulation
- 7: Volume
- 10: Pan
- 11: Expression
- 64: Sustain pedal
- 74: Filter cutoff (often)

### Pitch Bend
- Range: -8192 to 8191
- 0 = center (no bend)
- Negative = bend down, Positive = bend up

### Program Change
- Selects instrument (0-127)
- Mapping depends on synthesizer (General MIDI standard exists)

## Auto Note-Off

When `duration` is specified, the note is automatically turned off after the delay:

```python
yield {
    'event_type': 'note',
    'midi_note': 60,
    'velocity': 100,
    'duration': 1.0  # Automatically turn off after 1 second
}
```

## Active Note Cleanup

The engine tracks active notes and sends note-off for all active notes on shutdown, preventing stuck notes.

## Testing

Run tests with:
```bash
python -m pytest midi_out_stream/tests/
```

Or run directly:
```bash
python midi_out_stream/tests/test_midi_out_stream.py
```

## Virtual Ports

Virtual ports allow routing MIDI within the same computer:
- **macOS**: Supported via CoreMIDI
- **Linux**: Supported via ALSA
- **Windows**: Not supported (use loopMIDI or similar)

## Notes

- MIDI channels are 0-indexed internally (0-15) but displayed as 1-16
- All values are clamped to valid MIDI ranges
- The consumer blocks until the control stream is exhausted
- Scheduled note-offs run in a background thread

## Dependencies

- **mido**: High-level MIDI library for Python
- **python-rtmidi**: RtMidi backend for mido (low-latency I/O)
