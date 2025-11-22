"""
VIZ_STREAM (stream_visualizer)

Real-time visualization consumer for stream data. Creates live plots and
visualizations of stream parameters.
"""

from .core import (
    viz_stream_consumer,
    VizConfig,
    PlotType,
)

__version__ = "0.1.0"
__all__ = ["viz_stream_consumer", "VizConfig", "PlotType"]
