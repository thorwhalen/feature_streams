# SYNTH_STREAM (dict_to_audio)

Consume a stream of control dictionaries and generate real-time audio output using a synthesis engine. Provides low-latency, parameter-driven sound generation.

## Features

- Real-time audio synthesis
- Multiple waveforms (sine, saw, square, triangle)
- Low-latency output (<50ms typical)
- Smooth parameter interpolation (no clicks/pops)
- Thread-safe parameter updates
- Configurable sample rate and block size

## Installation

Required dependencies:
```bash
pip install numpy sounddevice
```

Optional (for advanced filtering):
```bash
pip install scipy
```

## Usage

### Basic Usage

```python
from synth_stream import synth_stream_consumer
import time

def control_stream_generator():
    """Generate control parameters."""
    for i in range(100):
        yield {
            'pitch_hz': 440.0,  # A4
            'amplitude': 0.5,
            'waveform_type': 'sine'
        }
        time.sleep(0.05)  # 20Hz update rate

# Start synthesis
synth_stream_consumer(control_stream_generator())
```

### With Input Stream

Combine with an input stream package:

```python
from trackpad_stream import trackpad_stream
from synth_stream import synth_stream_consumer

def control_mapper():
    """Map trackpad to synth controls."""
    for event in trackpad_stream():
        yield {
            'pitch_hz': 200 + (event['x_norm'] * 600),  # 200-800 Hz
            'amplitude': event['y_norm'],
            'waveform_type': 'sine' if not event['left_click'] else 'square'
        }

synth_stream_consumer(control_mapper())
```

### Custom Configuration

```python
from synth_stream import synth_stream_consumer, SynthConfig

config = SynthConfig(
    sample_rate=48000,
    block_size=256,  # Lower = less latency, higher CPU
    channels=1,      # Mono
    interpolation_alpha=0.2  # Faster parameter changes
)

synth_stream_consumer(my_control_stream(), config)
```

## Data Contract (Input Stream - Control Vector)

The consumer expects control dictionaries with these fields:

```python
{
    'timestamp': float,              # Unix timestamp (optional, not used)
    'pitch_hz': float,               # Fundamental frequency (20-20000 Hz)
    'amplitude': float,              # Volume [0.0, 1.0]
    'waveform_type': str,            # 'sine'|'saw'|'square'|'triangle'
    'filter_cutoff_hz': float,       # (reserved for future filtering)
    'filter_resonance': float,       # (reserved for future filtering)
}
```

All fields are optional. Missing fields retain their previous values.

## Supported Waveforms

- **sine**: Pure sine wave (smooth, fundamental tone)
- **saw**: Sawtooth wave (bright, harmonic-rich)
- **square**: Square wave (hollow, odd harmonics)
- **triangle**: Triangle wave (mellow, fewer harmonics)

## Example: Keyboard-Controlled Synth

```python
from keyboard_stream import keyboard_stream
from synth_stream import synth_stream_consumer
import time

# Track active notes
active_notes = {}

def keyboard_to_synth():
    """Map keyboard events to synth control."""
    for event in keyboard_stream():
        if event['event_type'] == 'press' and event['midi_note']:
            # Convert MIDI note to frequency
            note = event['midi_note']
            freq = 440 * (2 ** ((note - 69) / 12))
            active_notes[note] = freq

        elif event['event_type'] == 'release' and event['midi_note']:
            active_notes.pop(event['midi_note'], None)

        # Play highest active note (or silence)
        if active_notes:
            pitch_hz = max(active_notes.values())
            amplitude = 0.7
        else:
            pitch_hz = 440.0
            amplitude = 0.0  # Silence

        yield {
            'pitch_hz': pitch_hz,
            'amplitude': amplitude,
            'waveform_type': 'square'
        }

synth_stream_consumer(keyboard_to_synth())
```

## Parameter Interpolation

To prevent audio clicks and pops, parameter changes are smoothed using linear interpolation:

- `interpolation_alpha=0.1` (default): Slow, very smooth transitions
- `interpolation_alpha=0.5`: Medium speed
- `interpolation_alpha=1.0`: Instant (no interpolation, may click)

The interpolation formula:
```
current = current + alpha * (target - current)
```

## Audio Configuration

### Sample Rate
- 44100 Hz (default): CD quality
- 48000 Hz: Professional audio
- Higher rates = better quality, more CPU

### Block Size
- 512 samples (default): Good balance
- 256 samples: Lower latency, higher CPU
- 1024 samples: Higher latency, lower CPU

Latency ≈ `block_size / sample_rate` seconds

## Testing

Run tests with:
```bash
python -m pytest synth_stream/tests/
```

Or run directly:
```bash
python synth_stream/tests/test_synth_stream.py
```

## Notes

- Requires `numpy` and `sounddevice`
- Audio output runs in a separate thread (callback-based)
- Parameter updates are thread-safe
- The consumer blocks until the control stream is exhausted
- Press Ctrl+C to interrupt

## Dependencies

- **numpy**: Fast array operations for DSP
- **sounddevice**: Low-latency audio I/O
- **scipy** (optional): For advanced filtering
