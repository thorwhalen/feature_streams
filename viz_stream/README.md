# VIZ_STREAM (stream_visualizer)

Real-time visualization consumer for stream data. Creates live plots and visualizations of stream parameters.

## Features

- Real-time line plots
- Scatter plots
- Multiple field visualization
- Auto-scaling axes
- Configurable window size
- Live updates

## Installation

Required dependencies:
```bash
pip install matplotlib
```

## Usage

### Basic Line Plot

```python
from trackpad_stream import trackpad_stream
from viz_stream import viz_stream_consumer, VizConfig, PlotType

config = VizConfig(
    fields=['x_norm', 'y_norm'],
    plot_type=PlotType.LINE,
    window_size=200,
    title="Trackpad Position"
)

viz_stream_consumer(trackpad_stream(), config)
```

### Monitor Stream Statistics

```python
from util import monitor_stream
from trackpad_stream import trackpad_stream
from viz_stream import viz_stream_consumer, VizConfig

config = VizConfig(
    fields=['_stats.rate_hz'],
    title="Stream Rate",
    ylabel="Hz"
)

monitored = monitor_stream(trackpad_stream())
viz_stream_consumer(monitored, config)
```

### Audio Feature Visualization

```python
from audio_input_stream import audio_input_stream
from viz_stream import viz_stream_consumer, VizConfig

config = VizConfig(
    fields=['pitch_hz', 'loudness_norm', 'spectral_centroid_norm'],
    window_size=300,
    title="Audio Features"
)

viz_stream_consumer(audio_input_stream(), config)
```

## Configuration

```python
VizConfig(
    plot_type=PlotType.LINE,  # LINE, SCATTER, or BAR
    fields=['field1', 'field2'],  # Fields to visualize
    window_size=200,  # Number of points to display
    update_interval=50,  # Update interval in ms
    title="My Plot",
    ylabel="Value",
    y_range=(0, 1)  # Fixed Y range, or None for auto
)
```

## Plot Types

### Line Plot
```python
PlotType.LINE
```
Best for continuous data, smooth trends.

### Scatter Plot
```python
PlotType.SCATTER
```
Best for discrete events, sparse data.

## Nested Field Access

Access nested fields using dot notation:

```python
# Visualize stream statistics
config = VizConfig(
    fields=['_stats.rate_hz', '_stats.count']
)
```

## Examples

### Visualize Gamepad Axes

```python
from gamepad_stream import gamepad_stream
from viz_stream import viz_stream_consumer, VizConfig

config = VizConfig(
    fields=['left_stick_x', 'left_stick_y', 'right_stick_x', 'right_stick_y'],
    y_range=(-1, 1),
    title="Gamepad Axes"
)

viz_stream_consumer(gamepad_stream(), config)
```

### Keyboard Velocity Tracking

```python
from keyboard_stream import keyboard_stream
from viz_stream import viz_stream_consumer, VizConfig, PlotType

config = VizConfig(
    fields=['midi_velocity'],
    plot_type=PlotType.SCATTER,
    title="Keyboard Velocity"
)

viz_stream_consumer(keyboard_stream(), config)
```

## Notes

- The visualization runs in a blocking matplotlib window
- Press Ctrl+C in terminal to stop
- Window size controls how many points are displayed (older points scroll off)
- Update interval controls refresh rate (lower = smoother but more CPU)

## Dependencies

- **matplotlib**: Plotting library
