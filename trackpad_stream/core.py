"""
Core implementation for trackpad/mouse streaming.
"""

import sys
import time
from typing import Iterator, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pynput import mouse
import warnings

# Import parent util module
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp, normalize, RateLimiter


@dataclass
class TrackpadConfig:
    """Configuration for trackpad stream."""
    rate_hz: float = 60.0
    enable_mac_gestures: bool = True
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    normalize_coords: bool = True


def get_screen_bounds() -> Tuple[int, int]:
    """
    Get screen dimensions.

    Returns:
        Tuple[int, int]: (width, height) in pixels
    """
    # Try to get screen size from system
    try:
        if sys.platform == "darwin":
            # macOS
            from AppKit import NSScreen
            screen = NSScreen.mainScreen()
            frame = screen.frame()
            return int(frame.size.width), int(frame.size.height)
        elif sys.platform == "win32":
            # Windows
            import ctypes
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        else:
            # Linux - try Xlib
            try:
                from Xlib import display
                d = display.Display()
                screen = d.screen()
                return screen.width_in_pixels, screen.height_in_pixels
            except:
                pass
    except Exception as e:
        warnings.warn(f"Could not get screen bounds: {e}")

    # Default fallback
    return 1920, 1080


def get_mac_gestures():
    """
    Get Mac trackpad gesture events (pinch, rotate, swipe).

    Returns:
        Dict with gesture data or None if not on Mac
    """
    if sys.platform != "darwin":
        return None

    try:
        from AppKit import NSEvent, NSEventTypeMagnify, NSEventTypeRotate, NSEventTypeSwipe
        # This would need to be integrated with NSEvent monitoring
        # For now, return default values
        return {
            'pinch_magnification': 0.0,
            'rotation_degrees': 0.0,
            'swipe_direction': None,
        }
    except ImportError:
        warnings.warn("pyobjc-framework-Cocoa not installed, Mac gestures disabled")
        return {
            'pinch_magnification': 0.0,
            'rotation_degrees': 0.0,
            'swipe_direction': None,
        }


class TrackpadStreamState:
    """Maintains current state of trackpad/mouse."""

    def __init__(self, config: TrackpadConfig):
        self.config = config
        self.x = 0
        self.y = 0
        self.left_click = False
        self.right_click = False
        self.scroll_delta_x = 0.0
        self.scroll_delta_y = 0.0

        # Get screen bounds
        if config.screen_width and config.screen_height:
            self.screen_width = config.screen_width
            self.screen_height = config.screen_height
        else:
            self.screen_width, self.screen_height = get_screen_bounds()

    def on_move(self, x, y):
        """Callback for mouse movement."""
        self.x = x
        self.y = y

    def on_click(self, x, y, button, pressed):
        """Callback for mouse clicks."""
        self.x = x
        self.y = y
        if button == mouse.Button.left:
            self.left_click = pressed
        elif button == mouse.Button.right:
            self.right_click = pressed

    def on_scroll(self, x, y, dx, dy):
        """Callback for scroll events."""
        self.x = x
        self.y = y
        self.scroll_delta_x = dx
        self.scroll_delta_y = dy

    def get_stream_dict(self) -> Dict[str, Any]:
        """
        Generate current stream dictionary.

        Returns:
            Dict with all trackpad state
        """
        # Normalize coordinates if enabled
        if self.config.normalize_coords:
            x_norm = normalize(self.x, 0, self.screen_width)
            y_norm = normalize(self.y, 0, self.screen_height)
        else:
            x_norm = float(self.x) / self.screen_width
            y_norm = float(self.y) / self.screen_height

        result = {
            'timestamp': timestamp(),
            'x_norm': x_norm,
            'y_norm': y_norm,
            'x_raw': self.x,
            'y_raw': self.y,
            'left_click': self.left_click,
            'right_click': self.right_click,
            'scroll_delta_x': self.scroll_delta_x,
            'scroll_delta_y': self.scroll_delta_y,
        }

        # Add Mac gestures if enabled
        if self.config.enable_mac_gestures:
            gestures = get_mac_gestures()
            if gestures:
                result.update(gestures)
        else:
            # Provide default values
            result['pinch_magnification'] = 0.0
            result['rotation_degrees'] = 0.0
            result['swipe_direction'] = None

        # Reset scroll deltas after reading (they're event-based)
        self.scroll_delta_x = 0.0
        self.scroll_delta_y = 0.0

        return result


def trackpad_stream(config: Optional[TrackpadConfig] = None) -> Iterator[Dict[str, Any]]:
    """
    Generate stream of trackpad/mouse events.

    Args:
        config: Optional configuration (uses defaults if None)

    Yields:
        Dict: Stream items with trackpad state

    Example:
        >>> for item in trackpad_stream():
        ...     print(f"Position: ({item['x_norm']:.2f}, {item['y_norm']:.2f})")
        ...     if item['left_click']:
        ...         print("  Left click!")
    """
    if config is None:
        config = TrackpadConfig()

    state = TrackpadStreamState(config)
    limiter = RateLimiter(config.rate_hz)

    # Start mouse listener
    listener = mouse.Listener(
        on_move=state.on_move,
        on_click=state.on_click,
        on_scroll=state.on_scroll
    )
    listener.start()

    try:
        while True:
            limiter.wait()
            yield state.get_stream_dict()
    finally:
        listener.stop()
