# feature_streams

Live source raw features - Independent stream packages for creating and consuming real-time data streams.

## Overview

This repository contains **10 independent streaming packages** organized into categories:

### Input Streams (Creating Feature Streams)
Transform human-controllable input devices into streams of dictionaries:

1. **trackpad_stream** - Mouse/trackpad position, clicks, Mac gestures
2. **keyboard_stream** - Keyboard events with MIDI note mapping
3. **gamepad_stream** - Gamepad/joystick analog and digital inputs
4. **audio_input_stream** - Microphone input with pitch/loudness detection

### Output Streams (Consuming Control Streams)
Transform streams of dictionaries into audio/MIDI output:

5. **synth_stream** - Real-time audio synthesis
6. **tts_stream** - Text-to-speech output
7. **midi_out_stream** - MIDI message output
8. **viz_stream** - Real-time visualization plots

### Infrastructure Streams
Enable advanced streaming workflows:

9. **network_stream** - Stream data over TCP network
10. **Utilities** - Recording, playback, composition, transforms

## Installation

Each package has its own dependencies. Install what you need:

```bash
# Input streams
pip install pynput                    # trackpad_stream, keyboard_stream
pip install pygame                    # gamepad_stream
pip install numpy sounddevice aubio   # audio_input_stream

# Output streams
pip install numpy sounddevice scipy   # synth_stream
pip install pyttsx3                   # tts_stream
pip install mido python-rtmidi        # midi_out_stream
pip install matplotlib                # viz_stream

# network_stream has no dependencies (uses stdlib)
```

Or install everything:
```bash
pip install -r requirements.txt
```

## Quick Start

### Example 1: Trackpad → Synthesizer

```python
from trackpad_stream import trackpad_stream
from synth_stream import synth_stream_consumer

def trackpad_to_synth():
    """Map trackpad position to audio synthesis."""
    for event in trackpad_stream():
        yield {
            'pitch_hz': 200 + (event['x_norm'] * 600),  # 200-800 Hz
            'amplitude': event['y_norm'],                # Volume
            'waveform_type': 'sine'
        }

synth_stream_consumer(trackpad_to_synth())
```

### Example 2: Keyboard → MIDI

```python
from keyboard_stream import keyboard_stream
from midi_out_stream import midi_out_stream_consumer

def keyboard_to_midi():
    """Convert keyboard to MIDI notes."""
    for event in keyboard_stream():
        if event['midi_note'] is not None:
            yield {
                'event_type': 'note',
                'midi_note': event['midi_note'],
                'velocity': event['midi_velocity'] if event['event_type'] == 'press' else 0,
                'channel': 0
            }

midi_out_stream_consumer(keyboard_to_midi())
```

### Example 3: Gamepad → Speech

```python
from gamepad_stream import gamepad_stream
from tts_stream import tts_stream_consumer
import time

def gamepad_announcer():
    """Announce gamepad button presses."""
    last_time = 0
    for state in gamepad_stream():
        if time.time() - last_time > 1.0:  # Rate limit
            for button, pressed in state['button_states'].items():
                if pressed:
                    yield {'text': f"Button {button} pressed"}
                    last_time = time.time()
                    break

tts_stream_consumer(gamepad_announcer())
```

## Package Structure

Each package is independent and follows this structure:

```
package_name/
├── __init__.py          # Public API
├── core.py              # Implementation
├── README.md            # Package documentation
└── tests/
    └── test_*.py        # Tests
```

## Shared Utilities

### util.py - Core Utilities
- `timestamp()` - Get current Unix timestamp
- `normalize()` - Normalize values to [0, 1]
- `apply_deadzone()` - Dead-zone for analog inputs
- `RateLimiter` - Control stream rate
- `StreamBuffer` - Thread-safe stream buffering
- `interpolate_value()` - Smooth parameter transitions

### Recording & Playback
- `record_stream()` - Save stream to JSON lines file
- `playback_stream()` - Replay recorded stream

### Stream Composition
- `merge_streams()` - Merge multiple streams
- `broadcast_stream()` - Send to multiple consumers
- `filter_stream()` - Filter stream items
- `map_stream()` - Transform stream items
- `monitor_stream()` - Add statistics to stream

### transforms.py - Pre-built Transformers
- `linear_map()`, `exponential_map()` - Value mapping
- `midi_to_freq()`, `freq_to_midi()` - Musical conversions
- `quantize_to_scale()` - Musical scale quantization
- `SCALES` - Common musical scales
- `cartesian_to_polar()`, `polar_to_cartesian()` - Coordinate conversions
- `linear_to_db()`, `db_to_linear()` - dB conversions

## Data Contracts

All streams use dictionaries with consistent patterns:

**Input Streams** (device → dict):
- Always include `timestamp` field
- Normalized values in [0, 1] or [-1, 1]
- Boolean states for discrete inputs

**Output Streams** (dict → audio/MIDI):
- Consume dicts with control parameters
- Missing fields use previous/default values
- Thread-safe parameter updates

## Testing

Each package has its own tests:

```bash
# Test individual package
python trackpad_stream/tests/test_trackpad_stream.py

# Or use pytest
pytest trackpad_stream/tests/
```

## Examples

Complete example applications in `examples/`:

- **theremin.py** - Classic theremin (trackpad → synth)
- **keyboard_sampler.py** - Multi-voice keyboard synthesizer
- **gamepad_dj.py** - Gamepad DJ controller (MIDI CC)
- **voice_theremin.py** - Voice-controlled synthesizer
- **stream_recorder.py** - Record/playback utility

Run examples:
```bash
python examples/theremin.py
python examples/voice_theremin.py
```

## CLI Tools

Some packages have command-line interfaces:

```bash
# Preview trackpad stream
python -m trackpad_stream --preview

# Record audio features
python -m audio_input_stream --record features.jsonl --duration 10

# List audio devices
python -m audio_input_stream --list-devices
```

## Documentation

Each package has detailed documentation in its README:

- [trackpad_stream/README.md](trackpad_stream/README.md)
- [keyboard_stream/README.md](keyboard_stream/README.md)
- [gamepad_stream/README.md](gamepad_stream/README.md)
- [audio_input_stream/README.md](audio_input_stream/README.md)
- [synth_stream/README.md](synth_stream/README.md)
- [tts_stream/README.md](tts_stream/README.md)
- [midi_out_stream/README.md](midi_out_stream/README.md)
- [viz_stream/README.md](viz_stream/README.md)
- [network_stream/README.md](network_stream/README.md)

See also: [Stream Project Specifications](misc/docs/stream_project_specs.md)

## Design Philosophy

### Independence
Each package is self-contained and can be moved to its own repository. No inter-package dependencies.

### Composability
Packages use a common streaming pattern (iterators of dicts) making them easy to chain and transform.

### Simplicity
Minimal dependencies, straightforward APIs, clear data contracts.

### Real-time
Designed for live, interactive use with low latency.

## Advanced Usage

### Transformation Pipelines

Use intermediate transformations between input and output:

```python
def transform_stream(input_stream):
    """Transform input before output."""
    for item in input_stream:
        # Apply transformations
        transformed = {
            'pitch_hz': item['x_norm'] * 440 + 220,
            'amplitude': item['y_norm'] ** 2,  # Non-linear
            'waveform_type': 'square' if item['left_click'] else 'sine'
        }
        yield transformed

synth_stream_consumer(transform_stream(trackpad_stream()))
```

### Multiple Consumers

Split a stream to multiple outputs:

```python
from itertools import tee

input_stream = keyboard_stream()
stream1, stream2 = tee(input_stream)

# Run consumers in threads
Thread(target=lambda: synth_stream_consumer(stream1)).start()
Thread(target=lambda: midi_out_stream_consumer(stream2)).start()
```

## Contributing

Each package is designed to eventually become its own repository. When contributing:

1. Keep packages independent
2. Follow existing data contract patterns
3. Add tests for new features
4. Update package README

## License

See LICENSE file.

## Related Projects

- [stream2py](https://github.com/i2mint/stream2py) - Stream processing patterns
- [meshed](https://github.com/i2mint/meshed) - Data flow composition
- [qh](https://github.com/i2mint/qh) - Testing utilities
