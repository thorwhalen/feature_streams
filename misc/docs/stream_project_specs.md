# Stream Projects: Input and Output Specifications

This document contains specifications for INDEPENDENT projects that create input streams (streams of dicts from human-controllable sources) and output streams (consuming streams of dicts to produce live audio/sound).

---

## INPUT STREAM PROJECTS

### Project 1: TRACKPAD_STREAM

**Project Name:** TRACKPAD_STREAM
**Alternative Name:** xy_gestures

**Function:** Capture real-time mouse/trackpad movement, clicks, and Mac-specific trackpad gestures (scroll, pinch, rotate, swipe), converting them into a high-frequency feature stream suitable for live audio control.

#### I. Mandate and Required Tools

| Tool | Role in Project | Justification |
|------|----------------|---------------|
| **pynput** | Core I/O | Cross-platform listener for mouse position and button events. Use `pynput.mouse.Listener` for event callbacks. |
| **pyobjc-framework-Cocoa** | Mac Trackpad Gestures | Access NSEvent to capture high-resolution trackpad gestures (pinch/magnification, rotation, swipe) that pynput doesn't provide. Use `NSEvent.addGlobalMonitorForEventsMatchingMask_handler_()` for gesture events. |
| **stream2py** | Stream Architecture | Follow stream2py patterns for creating consistent stream interfaces with proper timestamping. |
| **qh.testing** | Testing Infrastructure | Use `qh.testing.service_running` context manager to spawn and teardown test processes. |

#### II. Implementation Requirements

1. **Create Core Stream Generator:**
   - Implement a generator function that yields dictionaries at ~60Hz
   - Normalize screen coordinates to [0.0, 1.0] range
   - Handle both event-driven updates (clicks, gestures) and polled updates (position)

2. **Mac Trackpad Integration:**
   - Use `NSEvent` to capture:
     - `NSEventTypeMagnify` for pinch-to-zoom
     - `NSEventTypeRotate` for rotation gestures
     - `NSEventTypeSwipe` for directional swipes
     - `NSEventTypeScrollWheel` for high-precision scrolling
   - Provide graceful degradation on non-Mac platforms (disable gesture features)

3. **Data Normalization:**
   - Query screen dimensions using `pynput` or `AppKit.NSScreen`
   - Normalize X/Y coordinates relative to main screen bounds
   - Apply smoothing/filtering options for jitter reduction

#### III. Data Contract (Output Stream)

Stream of dictionaries published at ~60Hz:

```python
{
    'timestamp': float,              # Unix timestamp (time.time())
    'x_norm': float,                 # Normalized X position [0.0, 1.0]
    'y_norm': float,                 # Normalized Y position [0.0, 1.0]
    'x_raw': int,                    # Raw X pixel coordinate
    'y_raw': int,                    # Raw Y pixel coordinate
    'left_click': bool,              # Left button state
    'right_click': bool,             # Right button state
    'scroll_delta_x': float,         # Horizontal scroll delta
    'scroll_delta_y': float,         # Vertical scroll delta
    'pinch_magnification': float,    # Pinch delta (Mac only, 0.0 if not pinching)
    'rotation_degrees': float,       # Rotation delta in degrees (Mac only)
    'swipe_direction': str,          # 'left'|'right'|'up'|'down'|None (Mac only)
}
```

#### IV. Testing Plan

**Testing Requirements:**
1. **Unit Tests (Normalization):**
   - Test coordinate normalization with mock screen dimensions
   - Verify boundary conditions (corners, edges)

2. **Integration Tests (Live Stream):**
   - **Tool Usage:** Use `qh.testing.service_running` to spawn the stream service
   - **Procedure:**
     ```python
     from qh.testing import service_running

     # Start trackpad stream service in separate process
     with service_running(trackpad_stream_func, stream_config) as service:
         # Consumer process: collect stream items
         collected_items = []
         for item in service.stream_output():
             collected_items.append(item)
             if len(collected_items) >= 100:
                 break

         # Verify stream properties
         assert all('timestamp' in item for item in collected_items)
         assert all(0.0 <= item['x_norm'] <= 1.0 for item in collected_items)
     ```

3. **Simulated Input Tests:**
   - Use `pynput.mouse.Controller` to programmatically move mouse
   - Verify output stream reflects simulated movements
   - Test click state transitions

---

### Project 2: KEYBOARD_STREAM

**Project Name:** KEYBOARD_STREAM
**Alternative Name:** key_to_note

**Function:** Capture keyboard key presses and releases, converting them into a structured, time-stamped stream with optional MIDI note mapping for musical control.

#### I. Mandate and Required Tools

| Tool | Role in Project | Justification |
|------|----------------|---------------|
| **pynput.keyboard** | Core I/O | Event-driven keyboard listener with `on_press` and `on_release` callbacks. Handles special keys and modifiers. |
| **mido** | MIDI Mapping | Convert key names to MIDI note numbers. Use `mido` for standard MIDI note definitions. |
| **stream2py** | Stream Architecture | Consistent stream interface and timestamping patterns. |
| **queue.Queue** | Event Buffering | pynput callbacks run in separate thread; use thread-safe queue to pass events to main generator thread. |
| **qh.testing** | Testing Infrastructure | Use for dual-process testing scenarios. |

#### II. Implementation Requirements

1. **Key Mapping Configuration:**
   - Create configurable mapping: keyboard keys → MIDI notes
   - Default mapping: Home row (A-S-D-F-G-H-J-K) → C major scale (C4-C5)
   - Support for modifier keys (Shift for octave up, Ctrl for octave down)

2. **Event Processing:**
   - Use `pynput.keyboard.Listener` with callbacks
   - Queue events from listener thread to generator thread
   - Track key state (currently pressed keys) to avoid duplicate press events

3. **Stream Generation:**
   - Generator yields dict for each key event (press/release)
   - Include both raw key information and computed MIDI note

#### III. Data Contract (Output Stream)

Stream of dictionaries (event-driven, not periodic):

```python
{
    'timestamp': float,              # Unix timestamp
    'key': str,                      # Key identifier (e.g., 'a', 'shift', 'space')
    'event_type': str,               # 'press' or 'release'
    'midi_note': int or None,        # MIDI note number (60 = Middle C) or None
    'midi_velocity': int,            # 0-127, based on typing speed/pressure estimate
    'is_modifier': bool,             # True if Shift, Ctrl, Alt, Cmd
    'active_modifiers': list[str],   # Currently held modifier keys
    'octave_shift': int,             # Octave shift from modifiers (-2 to +2)
}
```

#### IV. Testing Plan

**Testing Requirements:**
1. **Key Mapping Tests:**
   - Verify MIDI note assignments for default layout
   - Test modifier key combinations (Shift+A should be different octave)

2. **Dual-Process Integration Test:**
   - **Tool Usage:** Use `qh.testing.service_running` for producer-consumer test
   - **Procedure:**
     ```python
     from qh.testing import service_running
     from pynput.keyboard import Controller, Key

     keyboard = Controller()

     with service_running(keyboard_stream_func) as service:
         # Simulate key sequence: C-E-G (C major chord)
         keyboard.press('a')  # C
         keyboard.press('s')  # D
         keyboard.press('d')  # E

         # Collect stream events
         events = list(service.stream_output(timeout=1.0))

         # Verify MIDI notes match expected sequence
         press_events = [e for e in events if e['event_type'] == 'press']
         assert press_events[0]['midi_note'] == 60  # C4
         assert press_events[1]['midi_note'] == 62  # D4
         assert press_events[2]['midi_note'] == 64  # E4
     ```

3. **Velocity Estimation Test:**
   - Test typing speed detection (time between key events)
   - Verify velocity values are in valid MIDI range (0-127)

---

### Project 3: GAMEPAD_STREAM

**Project Name:** GAMEPAD_STREAM
**Alternative Name:** joy_control

**Function:** Capture real-time gamepad/joystick input (analog sticks, buttons, triggers, D-pad) and convert into a continuous stream suitable for expressive audio control.

#### I. Mandate and Required Tools

| Tool | Role in Project | Justification |
|------|----------------|---------------|
| **pygame** | Core I/O | `pygame.joystick` module provides comprehensive gamepad support across platforms. Handles initialization, event polling, and device enumeration. |
| **inputs** (alternative) | Fallback Option | Pure-Python gamepad library if pygame too heavy. Use only if pygame is unavailable. |
| **stream2py** | Stream Architecture | Consistent streaming patterns and timestamping. |
| **qh.testing** | Testing Infrastructure | Multi-process testing for stream verification. |

#### II. Implementation Requirements

1. **Gamepad Detection and Initialization:**
   - Use `pygame.joystick.init()` and `pygame.joystick.get_count()`
   - Support multiple connected gamepads (configurable device index)
   - Graceful handling of device connection/disconnection

2. **Input Processing:**
   - Poll gamepad state in main loop (not event-based)
   - Sample at consistent rate (e.g., 60Hz or 120Hz)
   - Normalize all analog inputs to [-1.0, 1.0] or [0.0, 1.0] depending on type

3. **Input Mapping:**
   - Analog sticks (2 axes each): X/Y values in [-1.0, 1.0]
   - Triggers (analog): values in [0.0, 1.0]
   - Buttons: boolean states
   - D-pad/Hat: discrete direction values

4. **Dead-zone Handling:**
   - Apply configurable dead-zone to analog sticks (default 0.1)
   - Prevent drift from centered position

#### III. Data Contract (Output Stream)

Stream of dictionaries at ~60-120Hz:

```python
{
    'timestamp': float,              # Unix timestamp
    'device_id': int,                # Gamepad device index
    'left_stick_x': float,           # Left analog X [-1.0, 1.0]
    'left_stick_y': float,           # Left analog Y [-1.0, 1.0]
    'right_stick_x': float,          # Right analog X [-1.0, 1.0]
    'right_stick_y': float,          # Right analog Y [-1.0, 1.0]
    'left_trigger': float,           # Left trigger [0.0, 1.0]
    'right_trigger': float,          # Right trigger [0.0, 1.0]
    'button_states': dict,           # {'a': True, 'b': False, ...}
    'dpad_x': int,                   # -1 (left), 0 (center), 1 (right)
    'dpad_y': int,                   # -1 (down), 0 (center), 1 (up)
}
```

#### IV. Testing Plan

**Testing Requirements:**
1. **Mock Gamepad Tests:**
   - Create mock gamepad state generator
   - Test normalization and dead-zone logic

2. **Dual-Process Stream Test:**
   - **Tool Usage:** Use `qh.testing.service_running`
   - **Procedure:**
     ```python
     from qh.testing import service_running

     # Mock gamepad state generator (simulates stick movement)
     def mock_gamepad_states():
         for i in range(100):
             yield {
                 'timestamp': time.time(),
                 'left_stick_x': math.sin(i * 0.1),  # Smooth oscillation
                 'left_stick_y': 0.0,
                 # ... other fields
             }

     with service_running(gamepad_stream_func, mock_input=mock_gamepad_states()) as service:
         # Consumer: verify stream rate and value ranges
         items = list(service.stream_output(max_items=50))

         # Verify sample rate (~60Hz, within tolerance)
         time_deltas = [items[i+1]['timestamp'] - items[i]['timestamp']
                        for i in range(len(items)-1)]
         avg_delta = sum(time_deltas) / len(time_deltas)
         assert 0.015 < avg_delta < 0.020  # ~60Hz ± tolerance

         # Verify value ranges
         assert all(-1.0 <= item['left_stick_x'] <= 1.0 for item in items)
     ```

3. **Physical Device Test Instructions:**
   - Provide manual test procedure for physical gamepad
   - Verify button mapping correctness for common controllers (Xbox, PS, Switch)

---

## OUTPUT STREAM PROJECTS

### Project 4: SYNTH_STREAM

**Project Name:** SYNTH_STREAM
**Alternative Name:** dict_to_audio

**Function:** Consume a stream of control dictionaries and generate real-time audio output using a synthesis engine. Provides low-latency, parameter-driven sound generation.

#### I. Mandate and Required Tools

| Tool | Role in Project | Justification |
|------|----------------|---------------|
| **sounddevice** | Audio I/O | Low-latency, cross-platform audio output using NumPy arrays. Preferred over PyAudio for better performance. |
| **numpy** | DSP Computation | Fast array operations for audio buffer generation and signal processing. |
| **scipy.signal** | Audio Processing | Filter design, waveform generation, envelope shaping. |
| **pyo** (optional) | Advanced Synthesis | Full-featured synthesis engine if complex DSP needed. Use only if basic numpy synthesis insufficient. |
| **stream2py** | Stream Consumption | Consume input control streams with consistent interface. |
| **qh.testing** | Testing Infrastructure | Dual-process testing (control stream → audio verification). |

#### II. Implementation Requirements

1. **Audio Engine Setup:**
   - Initialize `sounddevice.OutputStream` with callback function
   - Use sample rate of 44100 Hz or 48000 Hz
   - Configure block size for low latency (e.g., 512 or 1024 samples)

2. **Synthesis Core:**
   - Implement basic waveform generators: sine, saw, square, triangle
   - Support frequency and amplitude modulation from control stream
   - Use numpy for efficient buffer generation

3. **Control Stream Integration:**
   - Run control stream consumer in separate thread
   - Thread-safe parameter updates (use locks or atomic operations)
   - Interpolate parameter changes to avoid audio clicks/pops

4. **Parameter Mapping:**
   - Map `pitch_hz` → oscillator frequency
   - Map `amplitude` → output volume
   - Map `filter_cutoff_hz` → low-pass filter (if implemented)
   - Map `waveform_type` → waveform selection

#### III. Data Contract (Input Stream - Control Vector)

Consumes stream of dictionaries at variable rate (e.g., 20-60Hz):

```python
{
    'timestamp': float,              # Unix timestamp
    'pitch_hz': float,               # Fundamental frequency (20-20000 Hz)
    'amplitude': float,              # Volume [0.0, 1.0]
    'waveform_type': str,            # 'sine'|'saw'|'square'|'triangle'
    'filter_cutoff_hz': float,       # Low-pass filter cutoff (optional)
    'filter_resonance': float,       # Filter Q factor (optional)
    'envelope_attack': float,        # Attack time in seconds (optional)
    'envelope_release': float,       # Release time in seconds (optional)
}
```

#### IV. Testing Plan

**Testing Requirements:**
1. **Waveform Generation Tests:**
   - Generate known waveforms, capture output buffers
   - Use `scipy.fft` to verify frequency content
   - Verify DC offset is minimal (< 0.01)

2. **Dual-Process Test (Control → Audio):**
   - **Tool Usage:** Use `qh.testing.service_running` to spawn both processes
   - **Procedure:**
     ```python
     from qh.testing import service_running
     import scipy.fft

     # Process A: Generate control stream (440Hz sweep to 880Hz)
     def control_stream_generator():
         for i in range(100):
             yield {
                 'timestamp': time.time(),
                 'pitch_hz': 440 + (440 * i / 100),  # Linear sweep
                 'amplitude': 0.5,
                 'waveform_type': 'sine',
             }
             time.sleep(0.05)  # 20Hz update rate

     # Process B: SYNTH_STREAM consumer (with mock audio output)
     with service_running(synth_stream_func,
                         input_stream=control_stream_generator(),
                         mock_audio=True) as service:

         # Capture audio buffers over test duration
         audio_buffers = service.get_audio_buffers(duration=5.0)

         # Verify frequency sweep in captured audio
         concatenated = np.concatenate(audio_buffers)
         spectrum = scipy.fft.rfft(concatenated)
         peak_freq = scipy.fft.rfftfreq(len(concatenated), 1/44100)[np.argmax(np.abs(spectrum))]

         # Verify peak frequency is in expected range (440-880 Hz)
         assert 400 < peak_freq < 900
     ```

3. **Latency Test:**
   - Measure time from control dict update to audio output change
   - Target: < 50ms latency
   - Use timestamp comparison between control stream and audio analysis

---

### Project 5: TTS_STREAM

**Project Name:** TTS_STREAM
**Alternative Name:** dict_to_speech

**Function:** Consume a stream of text dictionaries and generate real-time text-to-speech audio output. Supports dynamic parameter control (speed, pitch, voice selection).

#### I. Mandate and Required Tools

| Tool | Role in Project | Justification |
|------|----------------|---------------|
| **pyttsx3** | TTS Engine | Offline, cross-platform TTS with immediate response. Works without internet. Best for low-latency requirements. |
| **RealtimeTTS** (alternative) | Advanced TTS | Use if need for higher quality voices (supports multiple backends). Has streaming capabilities but may have higher latency. |
| **sounddevice** | Audio Output | Direct audio output control for custom playback handling. |
| **stream2py** | Stream Consumption | Consistent control stream interface. |
| **queue.Queue** | Text Buffering | Thread-safe queue for text items waiting to be spoken. |
| **qh.testing** | Testing Infrastructure | Producer-consumer testing setup. |

#### II. Implementation Requirements

1. **TTS Engine Setup:**
   - Initialize `pyttsx3.init()` with appropriate driver
   - Configure default voice, rate, and volume
   - Handle voice enumeration and selection

2. **Stream Processing:**
   - Consume text dicts from input stream
   - Queue text items for sequential speaking
   - Support interruption (clear queue on priority message)

3. **Dynamic Parameter Control:**
   - Support real-time rate adjustment (words per minute)
   - Support pitch/volume changes
   - Voice switching (if input dict specifies voice)

4. **Playback Management:**
   - Non-blocking speech synthesis (run in separate thread)
   - Track speaking state (idle/speaking)
   - Handle queue overflow (drop old items if queue too long)

#### III. Data Contract (Input Stream - Text Control)

Consumes stream of dictionaries at variable rate:

```python
{
    'timestamp': float,              # Unix timestamp
    'text': str,                     # Text to speak
    'rate': int,                     # Speaking rate in WPM (50-300), optional
    'volume': float,                 # Volume [0.0, 1.0], optional
    'pitch': float,                  # Pitch adjustment [-1.0, 1.0], optional (not all engines support)
    'voice_id': str or None,         # Specific voice identifier, optional
    'priority': int,                 # 0=normal, 1=high (interrupts current), optional
    'language': str,                 # Language code (e.g., 'en-US'), optional
}
```

#### IV. Testing Plan

**Testing Requirements:**
1. **Voice Enumeration Test:**
   - Verify available voices can be listed
   - Test voice switching functionality

2. **Dual-Process Test (Text Stream → Speech):**
   - **Tool Usage:** Use `qh.testing.service_running`
   - **Procedure:**
     ```python
     from qh.testing import service_running

     # Process A: Text stream generator
     def text_stream_generator():
         texts = ["Hello world", "Testing one two three", "Speech synthesis active"]
         for text in texts:
             yield {
                 'timestamp': time.time(),
                 'text': text,
                 'rate': 150,
                 'volume': 0.8,
             }
             time.sleep(1.0)

     # Process B: TTS_STREAM consumer (with audio capture)
     with service_running(tts_stream_func,
                         input_stream=text_stream_generator(),
                         capture_audio=True) as service:

         # Wait for speech to complete
         service.wait_until_idle(timeout=10.0)

         # Verify audio was generated
         audio_data = service.get_captured_audio()
         assert len(audio_data) > 0

         # Verify speech events occurred
         events = service.get_speech_events()
         assert len([e for e in events if e['type'] == 'started']) == 3
         assert len([e for e in events if e['type'] == 'finished']) == 3
     ```

3. **Parameter Change Test:**
   - Send sequence with varying rates (50, 150, 300 WPM)
   - Verify rate changes are applied
   - Test priority interruption (high priority should cut off current speech)

---

### Project 6: MIDI_OUT_STREAM

**Project Name:** MIDI_OUT_STREAM
**Alternative Name:** dict_to_midi

**Function:** Consume a stream of musical control dictionaries and output MIDI messages to hardware/software synthesizers, DAWs, or virtual MIDI ports.

#### I. Mandate and Required Tools

| Tool | Role in Project | Justification |
|------|----------------|---------------|
| **mido** | MIDI Protocol | High-level MIDI message creation and port management. Clean Pythonic API. |
| **python-rtmidi** | MIDI Backend | RtMidi backend for mido, provides low-latency cross-platform MIDI I/O. |
| **stream2py** | Stream Consumption | Consistent control stream interface. |
| **time** | Timing Control | Precise message scheduling and timing. |
| **qh.testing** | Testing Infrastructure | Dual-process producer-consumer testing. |

#### II. Implementation Requirements

1. **MIDI Port Setup:**
   - Use `mido.get_output_names()` to enumerate available ports
   - Support virtual port creation (not available on Windows)
   - Allow port selection via configuration

2. **Message Generation:**
   - Convert control dicts to MIDI messages:
     - `note_on/note_off` for note events
     - `control_change` for continuous parameters
     - `pitch_bend` for pitch modulation
     - `program_change` for instrument selection

3. **Timing and Scheduling:**
   - Maintain accurate message timing
   - Support note duration handling (auto-generate note_off)
   - Queue messages if needed for precise timing

4. **State Management:**
   - Track active notes (send note_off for interrupted notes)
   - Handle all-notes-off on shutdown/error
   - Support MIDI channel selection (1-16)

#### III. Data Contract (Input Stream - Musical Control)

Consumes stream of dictionaries at variable rate:

```python
{
    'timestamp': float,              # Unix timestamp
    'event_type': str,               # 'note'|'cc'|'pitch_bend'|'program_change'

    # For note events:
    'midi_note': int,                # MIDI note number (0-127)
    'velocity': int,                 # Note velocity (0-127), 0 = note off
    'duration': float or None,       # Note duration in seconds (None = indefinite)

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

#### IV. Testing Plan

**Testing Requirements:**
1. **MIDI Message Format Tests:**
   - Verify correct message byte encoding
   - Test all message types (note, CC, pitch bend, etc.)
   - Verify channel encoding (0-indexed internally, 1-indexed externally)

2. **Dual-Process Test (Control Stream → MIDI):**
   - **Tool Usage:** Use `qh.testing.service_running` for producer-consumer setup
   - **Procedure:**
     ```python
     from qh.testing import service_running
     import mido

     # Process A: Musical control stream (play C major scale)
     def music_stream_generator():
         scale = [60, 62, 64, 65, 67, 69, 71, 72]  # C major
         for note in scale:
             yield {
                 'timestamp': time.time(),
                 'event_type': 'note',
                 'midi_note': note,
                 'velocity': 100,
                 'duration': 0.5,
                 'channel': 0,
             }
             time.sleep(0.5)

     # Process B: MIDI_OUT_STREAM (with virtual loopback port)
     with service_running(midi_out_stream_func,
                         input_stream=music_stream_generator(),
                         virtual_port='test_midi_out') as service:

         # Process C: MIDI input listener (verify messages)
         with mido.open_input('test_midi_out') as inport:
             messages = []
             for msg in inport:
                 messages.append(msg)
                 if len(messages) >= 16:  # 8 note_on + 8 note_off
                     break

             # Verify message sequence
             note_ons = [m for m in messages if m.type == 'note_on' and m.velocity > 0]
             assert len(note_ons) == 8
             assert [m.note for m in note_ons] == [60, 62, 64, 65, 67, 69, 71, 72]
     ```

3. **Timing Accuracy Test:**
   - Generate stream with precise timing requirements
   - Measure actual MIDI message timestamps
   - Verify timing jitter is < 10ms

4. **State Cleanup Test:**
   - Send note_on messages
   - Simulate crash/interrupt
   - Verify all notes are properly turned off (no stuck notes)

---

## Testing Infrastructure: qh.testing Usage

All projects must use `qh.testing` for multi-process testing. The key pattern is:

```python
from qh.testing import service_running

# service_running is a context manager that:
# 1. Spawns service in separate process
# 2. Handles process lifecycle (startup, teardown)
# 3. Provides communication channels between processes
# 4. Ensures clean shutdown even on errors

with service_running(stream_function, **config) as service:
    # Test code here
    # service.stream_output() - consume output stream
    # service.send_input() - send to input stream
    # service.wait_until() - wait for condition
    pass  # Automatic cleanup on context exit
```

This enables robust testing of streaming pipelines where producer and consumer run in separate processes, simulating real deployment scenarios.

---

## Integration Notes

These projects are designed to be **composable**:
- Input streams (TRACKPAD, KEYBOARD, GAMEPAD) can be combined/merged
- Output streams (SYNTH, TTS, MIDI) can consume from any input stream
- Use `meshed.slabs` (as mentioned in notes.md) for transformation pipelines

**Example Pipeline:**
```
GAMEPAD_STREAM → [transformation slab] → SYNTH_STREAM
                                       ↘ MIDI_OUT_STREAM
```

Where transformation slab maps gamepad axes to musical parameters (pitch, volume, filter, etc.).
