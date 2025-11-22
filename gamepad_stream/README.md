# GAMEPAD_STREAM (joy_control)

Capture real-time gamepad/joystick input (analog sticks, buttons, triggers, D-pad) and convert into a continuous stream suitable for expressive audio control.

## Features

- Cross-platform gamepad support (via pygame)
- Analog stick input with dead-zone handling
- Trigger support (analog inputs)
- Button state tracking
- D-pad/hat input
- Configurable sampling rate (default 60Hz)
- Support for multiple connected gamepads

## Installation

Required dependencies:
```bash
pip install pygame
```

## Usage

### List Available Gamepads

```python
from gamepad_stream import list_gamepads

gamepads = list_gamepads()
for gamepad in gamepads:
    print(gamepad)
# Output: "0: Xbox 360 Controller"
```

### Basic Usage

```python
from gamepad_stream import gamepad_stream

# Start streaming from first gamepad
for state in gamepad_stream():
    # Left stick for pitch control
    pitch = state['left_stick_x']  # -1.0 to 1.0

    # Right stick for filter control
    filter_cutoff = state['right_stick_y']

    # Triggers for volume
    volume = state['left_trigger']  # 0.0 to 1.0

    # Check button presses
    if state['button_states'].get('button_0'):
        print("Button A pressed!")
```

### Custom Configuration

```python
from gamepad_stream import gamepad_stream, GamepadConfig

config = GamepadConfig(
    device_id=0,           # First gamepad
    rate_hz=120.0,         # 120Hz sampling
    deadzone=0.15,         # Larger dead-zone
    enable_buttons=True,
    enable_axes=True,
    enable_hat=True
)

for state in gamepad_stream(config):
    # Process state
    pass
```

## Data Contract

Each stream item is a dictionary with the following fields:

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
    'button_states': dict,           # {'button_0': True, 'button_1': False, ...}
    'dpad_x': int,                   # -1 (left), 0 (center), 1 (right)
    'dpad_y': int,                   # -1 (down), 0 (center), 1 (up)
}
```

## Controller Mapping

Common gamepad layouts (Xbox/PlayStation style):

**Axes:**
- Axis 0: Left stick X
- Axis 1: Left stick Y
- Axis 2: Right stick X (or Left Trigger on some controllers)
- Axis 3: Right stick Y (or Right Trigger on some controllers)
- Axis 4: Left Trigger
- Axis 5: Right Trigger

**Buttons (Xbox layout):**
- Button 0: A
- Button 1: B
- Button 2: X
- Button 3: Y
- Button 4: Left Bumper
- Button 5: Right Bumper
- Button 6: Back/Select
- Button 7: Start
- Button 8: Left Stick Click
- Button 9: Right Stick Click

## Example: Audio Synthesizer Control

```python
from gamepad_stream import gamepad_stream

for state in gamepad_stream():
    # Map left stick to pitch (200-800 Hz)
    pitch_hz = 500 + (state['left_stick_x'] * 300)

    # Map right stick Y to filter cutoff
    filter_cutoff = 200 + ((state['right_stick_y'] + 1.0) / 2.0) * 2000

    # Triggers control volume
    volume = (state['left_trigger'] + state['right_trigger']) / 2.0

    # Button A toggles waveform
    if state['button_states'].get('button_0'):
        waveform = 'square'
    else:
        waveform = 'sine'

    # Send to synthesizer...
    print(f"Pitch: {pitch_hz:.1f} Hz, Filter: {filter_cutoff:.1f} Hz, Vol: {volume:.2f}")
```

## Dead-Zone Handling

The dead-zone prevents controller drift when sticks are centered:

- Values within dead-zone threshold → 0.0
- Values outside dead-zone → Re-scaled to full range

Default dead-zone is 0.1 (10% of stick range).

## Testing

Run tests with:
```bash
python -m pytest gamepad_stream/tests/
```

Or run directly:
```bash
python gamepad_stream/tests/test_gamepad_stream.py
```

## Notes

- Requires a gamepad to be connected for normal operation
- pygame must be installed for gamepad support
- The stream samples at a fixed rate (polled, not event-driven)
- Some controllers may have different axis/button mappings
- Use `list_gamepads()` to see connected devices

## Dependencies

- **pygame**: Cross-platform gamepad/joystick support
