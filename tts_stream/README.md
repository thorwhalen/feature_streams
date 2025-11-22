# TTS_STREAM (dict_to_speech)

Consume a stream of text dictionaries and generate real-time text-to-speech audio output. Supports dynamic parameter control (speed, pitch, voice selection).

## Features

- Real-time text-to-speech synthesis
- Offline operation (no internet required)
- Cross-platform support (Windows, macOS, Linux)
- Dynamic rate (speed) and volume control
- Voice selection support
- Priority message handling (interruptions)
- Asynchronous speech queue

## Installation

Required dependencies:
```bash
pip install pyttsx3
```

Platform-specific requirements:
- **Windows**: Uses SAPI5 (built-in)
- **macOS**: Uses NSSpeechSynthesizer (built-in)
- **Linux**: Requires espeak: `sudo apt-get install espeak`

## Usage

### Basic Usage

```python
from tts_stream import tts_stream_consumer
import time

def text_stream_generator():
    """Generate text to speak."""
    texts = ["Hello world", "Testing speech synthesis", "Goodbye"]
    for text in texts:
        yield {
            'text': text,
            'rate': 150,
            'volume': 0.8
        }
        time.sleep(2.0)

tts_stream_consumer(text_stream_generator())
```

### List Available Voices

```python
from tts_stream import list_voices

voices = list_voices()
for voice in voices:
    print(f"{voice['name']} ({voice['id']})")
```

### Custom Voice

```python
from tts_stream import tts_stream_consumer, TTSConfig, list_voices

# Get first available voice
voices = list_voices()
voice_id = voices[0]['id'] if voices else None

config = TTSConfig(
    default_rate=180,
    default_volume=0.9,
    default_voice=voice_id
)

def text_gen():
    yield {'text': "Speaking with custom voice", 'rate': 180}

tts_stream_consumer(text_gen(), config)
```

## Data Contract (Input Stream - Text Control)

The consumer expects dictionaries with these fields:

```python
{
    'timestamp': float,              # Unix timestamp (optional, not used)
    'text': str,                     # Text to speak
    'rate': int,                     # Speaking rate in WPM (50-300), optional
    'volume': float,                 # Volume [0.0, 1.0], optional
    'pitch': float,                  # Pitch adjustment (not supported by pyttsx3)
    'voice_id': str or None,         # Specific voice identifier, optional
    'priority': int,                 # 0=normal, 1=high (interrupts current), optional
    'language': str,                 # Language code (depends on voice), optional
}
```

Only the `text` field is required. Other fields are optional.

## Example: Keyboard-Triggered Speech

```python
from keyboard_stream import keyboard_stream
from tts_stream import tts_stream_consumer

# Map keys to words
key_to_word = {
    'a': "Alpha",
    's': "Sigma",
    'd': "Delta",
    'f': "Foxtrot",
}

def keyboard_to_speech():
    """Convert keyboard presses to speech."""
    for event in keyboard_stream():
        if event['event_type'] == 'press':
            key = event['key']
            if key in key_to_word:
                yield {
                    'text': key_to_word[key],
                    'rate': 150,
                    'priority': 1  # Interrupt previous
                }

tts_stream_consumer(keyboard_to_speech())
```

## Example: Gamepad State Announcer

```python
from gamepad_stream import gamepad_stream
from tts_stream import tts_stream_consumer
import time

def gamepad_announcer():
    """Announce gamepad button presses."""
    last_announce = 0

    for state in gamepad_stream():
        # Announce button presses (with rate limiting)
        if time.time() - last_announce > 1.0:
            for button, pressed in state['button_states'].items():
                if pressed:
                    yield {
                        'text': f"Button {button} pressed",
                        'rate': 180
                    }
                    last_announce = time.time()
                    break

tts_stream_consumer(gamepad_announcer())
```

## Priority and Interruption

Set `priority` field to control speech queue behavior:

- `priority=0` (default): Normal, queued speech
- `priority=1`: High priority, interrupts current speech and clears queue

```python
def urgent_message():
    yield {'text': 'Normal message', 'priority': 0}
    time.sleep(2)
    yield {'text': 'URGENT ALERT', 'priority': 1}  # Interrupts

tts_stream_consumer(urgent_message())
```

## Speech Queue

The engine maintains a queue of text items to speak:
- Default queue size: 10 items
- When queue is full, new items are dropped
- Configure with `TTSConfig(queue_max_size=20)`

## Rate (Speed) Control

Speaking rate in words per minute (WPM):
- 50-100: Very slow
- 100-150: Slow
- 150-200: Normal
- 200-250: Fast
- 250-300: Very fast

Values outside range are clamped.

## Testing

Run tests with:
```bash
python -m pytest tts_stream/tests/
```

Or run directly:
```bash
python tts_stream/tests/test_tts_stream.py
```

## Notes

- Speech is asynchronous (runs in background thread)
- The consumer blocks until the text stream is exhausted
- After stream ends, waits up to 5 seconds for final speech to complete
- pyttsx3 does not support pitch control (parameter ignored)
- Voice availability varies by platform

## Platform-Specific Notes

### macOS
- High-quality voices available
- Voices in System Preferences > Accessibility > Speech

### Windows
- Uses SAPI5 voices
- Additional voices available via Microsoft Speech Platform

### Linux
- Requires espeak or festival
- Quality varies, consider espeak-ng for better quality

## Dependencies

- **pyttsx3**: Cross-platform TTS engine
