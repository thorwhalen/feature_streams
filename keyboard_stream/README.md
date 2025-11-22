# KEYBOARD_STREAM (key_to_note)

Capture keyboard key presses and releases, converting them into a structured, time-stamped stream with optional MIDI note mapping for musical control.

## Features

- Event-driven keyboard capture (press/release)
- Configurable key-to-MIDI-note mapping
- Default C major scale mapping on home row (A-S-D-F-G-H-J-K)
- Modifier key support (Shift for octave up, Ctrl for octave down)
- Velocity estimation based on typing speed
- Duplicate key press prevention

## Installation

Required dependencies:
```bash
pip install pynput
```

## Usage

### Basic Usage

```python
from keyboard_stream import keyboard_stream

# Start streaming keyboard events
for event in keyboard_stream():
    if event['event_type'] == 'press' and event['midi_note']:
        print(f"Note {event['midi_note']} pressed with velocity {event['midi_velocity']}")
```

### Custom Key Mapping

```python
from keyboard_stream import keyboard_stream, KeyboardConfig

# Custom chromatic scale starting from C3
custom_mapping = {
    'z': 48, 'x': 49, 'c': 50, 'v': 51,  # C3, C#3, D3, D#3
    'b': 52, 'n': 53, 'm': 54,           # E3, F3, F#3
}

config = KeyboardConfig(
    key_to_note=custom_mapping,
    enable_velocity=True,
    velocity_range=(50, 120)
)

for event in keyboard_stream(config):
    # Process with custom mapping
    pass
```

## Data Contract

Each stream item is a dictionary with the following fields:

```python
{
    'timestamp': float,              # Unix timestamp
    'key': str,                      # Key identifier (e.g., 'a', 'shift', 'space')
    'event_type': str,               # 'press' or 'release'
    'midi_note': int or None,        # MIDI note number (60 = Middle C) or None
    'midi_velocity': int,            # 0-127, based on typing speed (0 for release)
    'is_modifier': bool,             # True if Shift, Ctrl, Alt, Cmd
    'active_modifiers': list[str],   # Currently held modifier keys
    'octave_shift': int,             # Octave shift from modifiers (-1, 0, +1, etc.)
}
```

## Default Key Mapping

Home row (C major scale):
- A → C4 (60)
- S → D4 (62)
- D → E4 (64)
- F → F4 (65)
- G → G4 (67)
- H → A4 (69)
- J → B4 (71)
- K → C5 (72)

Number row (chromatic):
- 1 → C4 (60), 2 → C#4 (61), 3 → D4 (62), etc.

Modifiers:
- Shift: +1 octave (add 12 to note)
- Ctrl: -1 octave (subtract 12 from note)

## Example: Simple Synthesizer Control

```python
from keyboard_stream import keyboard_stream

for event in keyboard_stream():
    if event['event_type'] == 'press' and event['midi_note']:
        # Convert MIDI note to frequency
        note = event['midi_note']
        freq = 440 * (2 ** ((note - 69) / 12))
        velocity = event['midi_velocity'] / 127.0

        print(f"Play {freq:.1f} Hz at volume {velocity:.2f}")
        # Send to synthesizer...

    elif event['event_type'] == 'release' and event['midi_note']:
        print(f"Stop note {event['midi_note']}")
        # Stop note in synthesizer...
```

## Velocity Estimation

The stream estimates velocity based on typing speed:
- Fast typing (< 0.1s between keys) → High velocity (127)
- Slow typing (> 0.5s between keys) → Low velocity (64)
- Medium speed → Linear interpolation

This provides dynamic expression in musical applications.

## Testing

Run tests with:
```bash
python -m pytest keyboard_stream/tests/
```

Or run the test file directly:
```bash
python keyboard_stream/tests/test_keyboard_stream.py
```

## Notes

- The stream is event-driven (yields only when keys are pressed/released)
- Modifier keys generate their own press/release events
- MIDI notes are clamped to valid range (0-127) when octave shifted
- Duplicate press events for held keys are suppressed

## Dependencies

- **pynput**: Cross-platform keyboard control and monitoring
