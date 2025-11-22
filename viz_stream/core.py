"""
Core implementation for stream visualization consumer.
"""

import sys
import os
from typing import Iterator, Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import warnings

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp

# Import visualization dependencies
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from collections import deque
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn("matplotlib not installed. Install with: pip install matplotlib")


class PlotType(Enum):
    """Supported plot types."""
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"


@dataclass
class VizConfig:
    """Configuration for visualization."""
    plot_type: PlotType = PlotType.LINE
    fields: List[str] = field(default_factory=lambda: ['value'])
    window_size: int = 200  # Number of points to display
    update_interval: int = 50  # Update interval in ms
    title: str = "Stream Visualization"
    ylabel: str = "Value"
    y_range: Optional[tuple] = None  # (min, max) or None for auto


class StreamVisualizer:
    """Real-time stream visualizer using matplotlib."""

    def __init__(self, config: VizConfig):
        if not MATPLOTLIB_AVAILABLE:
            raise RuntimeError("matplotlib not installed")

        self.config = config

        # Data buffers
        self.data_buffers = {
            field: deque(maxlen=config.window_size)
            for field in config.fields
        }
        self.time_buffer = deque(maxlen=config.window_size)

        # Setup plot
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.lines = {}

        if config.plot_type == PlotType.LINE:
            for field in config.fields:
                line, = self.ax.plot([], [], label=field)
                self.lines[field] = line
        elif config.plot_type == PlotType.SCATTER:
            for field in config.fields:
                scatter = self.ax.scatter([], [], label=field, alpha=0.6)
                self.lines[field] = scatter
        elif config.plot_type == PlotType.BAR:
            # Bar plot uses different approach
            pass

        self.ax.set_title(config.title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel(config.ylabel)
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)

        if config.y_range:
            self.ax.set_ylim(config.y_range)

        # Start time
        self.start_time = None

    def update_data(self, item: Dict[str, Any]):
        """Update data buffers with new item."""
        if self.start_time is None:
            self.start_time = item.get('timestamp', timestamp())

        # Get relative time
        current_time = item.get('timestamp', timestamp())
        relative_time = current_time - self.start_time
        self.time_buffer.append(relative_time)

        # Update data buffers
        for field in self.config.fields:
            value = item.get(field, 0.0)
            # Handle nested fields (e.g., '_stats.rate_hz')
            if '.' in field:
                parts = field.split('.')
                obj = item
                for part in parts:
                    obj = obj.get(part, {})
                    if not isinstance(obj, dict):
                        value = obj
                        break
                else:
                    value = 0.0
            self.data_buffers[field].append(value)

    def update_plot(self, frame=None):
        """Update plot with current data."""
        if len(self.time_buffer) == 0:
            return list(self.lines.values())

        times = list(self.time_buffer)

        if self.config.plot_type == PlotType.LINE:
            for field, line in self.lines.items():
                values = list(self.data_buffers[field])
                line.set_data(times, values)

            # Auto-scale axes
            self.ax.relim()
            self.ax.autoscale_view()

        elif self.config.plot_type == PlotType.SCATTER:
            for field, scatter in self.lines.items():
                values = list(self.data_buffers[field])
                scatter.set_offsets(list(zip(times, values)))

            # Auto-scale axes
            self.ax.relim()
            self.ax.autoscale_view()

        return list(self.lines.values())

    def show(self):
        """Show the plot window."""
        plt.show()


def viz_stream_consumer(
    stream: Iterator[Dict[str, Any]],
    config: Optional[VizConfig] = None
):
    """
    Consume stream and visualize data in real-time.

    Args:
        stream: Input stream iterator
        config: Optional visualization configuration

    Example:
        >>> from trackpad_stream import trackpad_stream
        >>> viz_stream_consumer(
        ...     trackpad_stream(),
        ...     VizConfig(fields=['x_norm', 'y_norm'], plot_type=PlotType.LINE)
        ... )
    """
    if config is None:
        config = VizConfig()

    visualizer = StreamVisualizer(config)

    # Iterator for animation
    def stream_iterator():
        for item in stream:
            visualizer.update_data(item)
            yield item

    # Create animation
    stream_iter = stream_iterator()

    def animate_func(frame):
        try:
            next(stream_iter)
        except StopIteration:
            pass
        return visualizer.update_plot(frame)

    anim = animation.FuncAnimation(
        visualizer.fig,
        animate_func,
        interval=config.update_interval,
        blit=False,
        cache_frame_data=False
    )

    visualizer.show()
