"""
GAMEPAD_STREAM (joy_control)

Capture real-time gamepad/joystick input (analog sticks, buttons, triggers, D-pad)
and convert into a continuous stream suitable for expressive audio control.
"""

from .core import (
    gamepad_stream,
    GamepadConfig,
    list_gamepads,
)

__version__ = "0.1.0"
__all__ = ["gamepad_stream", "GamepadConfig", "list_gamepads"]
