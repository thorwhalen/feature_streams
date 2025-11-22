# AUDIO_INPUT_STREAM (mic_features)

Capture live microphone/audio input and extract musical features in real-time, outputting them as a control stream.

## Features

- Real-time audio capture from microphone
- Pitch detection (fundamental frequency)
- Loudness measurement (RMS, dB)
- Spectral centroid (brightness)
- Voice activity detection
- Configurable sample rate and block size
- Optional aubio backend for better pitch detection

## Installation

Required dependencies:
```bash
pip install numpy sounddevice
```

Optional (for better pitch detection):
```bash
pip install aubio
```

Platform-specific:
- **Linux**: May need `portaudio`: `sudo apt-get install portaudio19-dev`
- **macOS**: Built-in CoreAudio support
- **Windows**: Built-in audio support

## Usage

### Basic Usage

```python
from audio_input_stream import audio_input_stream

# Start streaming audio features
for features in audio_input_stream():
    if features['is_voiced']:
        print(f"Pitch: {features['pitch_hz']:.1f} Hz")
        print(f"Loudness: {features['loudness_db']:.1f} dB")
```

### List Audio Devices

```python
from audio_input_stream import list_audio_devices

devices = list_audio_devices()
for device in devices:
    print(f"{device['id']}: {device['name']}")
```

### Custom Configuration

```python
from audio_input_stream import audio_input_stream, AudioInputConfig

config = AudioInputConfig(
    sample_rate=48000,
    block_size=2048,
    hop_size=512,
    device=0,  # Specific device ID
    channels=1
)

for features in audio_input_stream(config):
    # Process features
    pass
```

## Data Contract

Each stream item is a dictionary with the following fields:

```python
{
    'timestamp': float,              # Unix timestamp
    'pitch_hz': float,               # Detected pitch in Hz (0 if not detected)
    'pitch_confidence': float,       # Pitch confidence [0.0, 1.0]
    'loudness_db': float,            # Loudness in dB (negative values)
    'loudness_norm': float,          # Normalized loudness [0.0, 1.0]
    'spectral_centroid_hz': float,   # Spectral centroid in Hz
    'spectral_centroid_norm': float, # Normalized centroid [0.0, 1.0]
    'is_voiced': bool,               # True if pitch detected with confidence
    'rms': float,                    # Raw RMS energy
}
```

## Example: Voice-Controlled Synthesizer

```python
from audio_input_stream import audio_input_stream
from synth_stream import synth_stream_consumer

def voice_to_synth():
    """Control synthesizer with voice pitch and loudness."""
    for features in audio_input_stream():
        if features['is_voiced']:
            yield {
                'pitch_hz': features['pitch_hz'],
                'amplitude': features['loudness_norm'],
                'waveform_type': 'sine'
            }
        else:
            # Silence when not voiced
            yield {
                'pitch_hz': 440.0,
                'amplitude': 0.0,
                'waveform_type': 'sine'
            }

synth_stream_consumer(voice_to_synth())
```

## Example: Pitch to MIDI

```python
from audio_input_stream import audio_input_stream
from midi_out_stream import midi_out_stream_consumer
import math

def freq_to_midi(freq):
    """Convert frequency to MIDI note number."""
    return int(round(69 + 12 * math.log2(freq / 440.0)))

def voice_to_midi():
    """Convert voice pitch to MIDI notes."""
    last_note = None

    for features in audio_input_stream():
        if features['is_voiced'] and features['pitch_confidence'] > 0.7:
            note = freq_to_midi(features['pitch_hz'])
            velocity = int(features['loudness_norm'] * 127)

            # Send note on if different from last
            if note != last_note:
                if last_note is not None:
                    yield {'event_type': 'note', 'midi_note': last_note, 'velocity': 0}
                yield {'event_type': 'note', 'midi_note': note, 'velocity': velocity}
                last_note = note
        else:
            # Turn off last note if not voiced
            if last_note is not None:
                yield {'event_type': 'note', 'midi_note': last_note, 'velocity': 0}
                last_note = None

midi_out_stream_consumer(voice_to_midi())
```

## Feature Descriptions

### Pitch Detection
- **pitch_hz**: Fundamental frequency in Hz (0 if no pitch detected)
- **pitch_confidence**: Confidence score [0, 1] (higher = more reliable)
- Uses aubio if available, otherwise basic autocorrelation

### Loudness
- **loudness_db**: RMS energy in decibels (typically -60 to 0 dB)
- **loudness_norm**: Normalized to [0, 1] range (assumes -60dB to 0dB)
- **rms**: Raw root-mean-square energy

### Spectral Centroid
- **spectral_centroid_hz**: "Center of mass" of spectrum (brightness measure)
- Higher values = brighter/harsher sound
- Lower values = darker/warmer sound

### Voice Activity
- **is_voiced**: Boolean indicating if pitch detected with sufficient confidence
- Useful for gating effects or triggering events

## Configuration Parameters

### Sample Rate
- 44100 Hz (default): CD quality
- 48000 Hz: Professional audio
- Higher = better frequency resolution, more CPU

### Block Size
- 2048 samples (default): Good balance
- Larger = better low-frequency resolution
- Smaller = lower latency

### Hop Size
- 512 samples (default): 75% overlap
- Smaller = more updates, higher CPU
- Should be ≤ block_size

Latency ≈ `hop_size / sample_rate` seconds

## Testing

Run tests with:
```bash
python -m pytest audio_input_stream/tests/
```

Or run directly:
```bash
python audio_input_stream/tests/test_audio_input_stream.py
```

## Notes

- Requires working microphone/audio input
- aubio provides better pitch detection but is optional
- Pitch detection works best with monophonic (single note) input
- Background noise affects detection accuracy
- Use `pitch_confidence` to filter unreliable detections

## Dependencies

- **numpy**: Array operations for DSP
- **sounddevice**: Audio input capture
- **aubio** (optional): High-quality pitch detection
