"""
TRACKPAD_STREAM (xy_gestures)

Capture real-time mouse/trackpad movement, clicks, and Mac-specific trackpad gestures,
converting them into a high-frequency feature stream suitable for live audio control.
"""

from .core import (
    trackpad_stream,
    TrackpadConfig,
    get_screen_bounds,
)

__version__ = "0.1.0"
__all__ = ["trackpad_stream", "TrackpadConfig", "get_screen_bounds"]
