# TRACKPAD_STREAM (xy_gestures)

Capture real-time mouse/trackpad movement, clicks, and Mac-specific trackpad gestures, converting them into a high-frequency feature stream suitable for live audio control.

## Features

- Cross-platform mouse/trackpad position tracking
- Click detection (left/right buttons)
- Scroll event capture
- Mac trackpad gestures (pinch, rotate, swipe) when available
- Normalized coordinates [0.0, 1.0]
- Configurable stream rate (default 60Hz)

## Installation

Required dependencies:
```bash
pip install pynput
```

For Mac gesture support (optional):
```bash
pip install pyobjc-framework-Cocoa
```

## Usage

### Basic Usage

```python
from trackpad_stream import trackpad_stream

# Start streaming trackpad events
for event in trackpad_stream():
    print(f"Position: ({event['x_norm']:.2f}, {event['y_norm']:.2f})")
    if event['left_click']:
        print("Left click detected!")
```

### With Configuration

```python
from trackpad_stream import trackpad_stream, TrackpadConfig

config = TrackpadConfig(
    rate_hz=120.0,  # 120Hz update rate
    enable_mac_gestures=True,
    normalize_coords=True
)

for event in trackpad_stream(config):
    # Process event
    pass
```

## Data Contract

Each stream item is a dictionary with the following fields:

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
    'swipe_direction': str or None,  # 'left'|'right'|'up'|'down'|None (Mac only)
}
```

## Example: Audio Control

```python
from trackpad_stream import trackpad_stream

for event in trackpad_stream():
    # Map X position to pitch (200-800 Hz)
    pitch = 200 + (event['x_norm'] * 600)

    # Map Y position to volume
    volume = event['y_norm']

    # Use pinch for filter cutoff
    filter_cutoff = 200 + (event['pinch_magnification'] * 2000)

    # Send to synthesizer...
```

## Testing

Run tests with:
```bash
python -m pytest trackpad_stream/tests/
```

## Notes

- On Mac, gesture support requires `pyobjc-framework-Cocoa`
- Scroll deltas are event-based (reset to 0.0 after each read)
- Gestures default to neutral values (0.0/None) on non-Mac platforms
- The stream runs indefinitely until interrupted (Ctrl+C)

## Dependencies

- **pynput**: Cross-platform input device control
- **pyobjc-framework-Cocoa** (optional): Mac gesture support
