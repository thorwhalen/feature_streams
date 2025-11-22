"""
Core implementation for gamepad/joystick streaming.
"""

import sys
import os
from typing import Iterator, Dict, Any, Optional, List
from dataclasses import dataclass
import warnings

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp, apply_deadzone, RateLimiter

# Import pygame for gamepad support
try:
    import pygame
    import pygame.joystick
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    warnings.warn("pygame not installed. Install with: pip install pygame")


@dataclass
class GamepadConfig:
    """Configuration for gamepad stream."""
    device_id: int = 0
    rate_hz: float = 60.0
    deadzone: float = 0.1
    enable_buttons: bool = True
    enable_axes: bool = True
    enable_hat: bool = True


def list_gamepads() -> List[str]:
    """
    List available gamepad devices.

    Returns:
        List of gamepad names
    """
    if not PYGAME_AVAILABLE:
        return []

    pygame.init()
    pygame.joystick.init()

    gamepads = []
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        gamepads.append(f"{i}: {joystick.get_name()}")

    return gamepads


class GamepadStreamState:
    """Maintains current state of gamepad."""

    def __init__(self, config: GamepadConfig):
        self.config = config

        if not PYGAME_AVAILABLE:
            raise RuntimeError("pygame not installed")

        # Initialize pygame
        pygame.init()
        pygame.joystick.init()

        # Check device exists
        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No gamepad devices found")

        if config.device_id >= pygame.joystick.get_count():
            raise RuntimeError(f"Gamepad {config.device_id} not found")

        # Initialize joystick
        self.joystick = pygame.joystick.Joystick(config.device_id)
        self.joystick.init()

        # Get capabilities
        self.num_axes = self.joystick.get_numaxes()
        self.num_buttons = self.joystick.get_numbuttons()
        self.num_hats = self.joystick.get_numhats()

    def poll(self) -> Dict[str, Any]:
        """
        Poll current gamepad state.

        Returns:
            Dict with current gamepad state
        """
        # Process pygame events (required for joystick updates)
        pygame.event.pump()

        result = {
            'timestamp': timestamp(),
            'device_id': self.config.device_id,
        }

        # Read analog sticks (typically 4 axes: left X/Y, right X/Y)
        if self.config.enable_axes:
            # Map common gamepad axes
            left_stick_x = 0.0
            left_stick_y = 0.0
            right_stick_x = 0.0
            right_stick_y = 0.0
            left_trigger = 0.0
            right_trigger = 0.0

            if self.num_axes >= 2:
                left_stick_x = apply_deadzone(self.joystick.get_axis(0), self.config.deadzone)
                left_stick_y = apply_deadzone(self.joystick.get_axis(1), self.config.deadzone)

            if self.num_axes >= 4:
                right_stick_x = apply_deadzone(self.joystick.get_axis(2), self.config.deadzone)
                right_stick_y = apply_deadzone(self.joystick.get_axis(3), self.config.deadzone)

            # Triggers (axis 4 and 5 on many controllers, or buttons)
            if self.num_axes >= 5:
                # Convert from [-1, 1] to [0, 1] for triggers
                left_trigger = (self.joystick.get_axis(4) + 1.0) / 2.0
            if self.num_axes >= 6:
                right_trigger = (self.joystick.get_axis(5) + 1.0) / 2.0

            result.update({
                'left_stick_x': left_stick_x,
                'left_stick_y': left_stick_y,
                'right_stick_x': right_stick_x,
                'right_stick_y': right_stick_y,
                'left_trigger': left_trigger,
                'right_trigger': right_trigger,
            })

        # Read buttons
        if self.config.enable_buttons:
            button_states = {}
            for i in range(self.num_buttons):
                button_states[f'button_{i}'] = bool(self.joystick.get_button(i))
            result['button_states'] = button_states

        # Read D-pad/hat
        if self.config.enable_hat and self.num_hats > 0:
            hat = self.joystick.get_hat(0)  # (x, y) tuple
            result['dpad_x'] = hat[0]
            result['dpad_y'] = hat[1]
        else:
            result['dpad_x'] = 0
            result['dpad_y'] = 0

        return result

    def close(self):
        """Clean up gamepad resources."""
        if hasattr(self, 'joystick'):
            self.joystick.quit()
        pygame.quit()


def gamepad_stream(config: Optional[GamepadConfig] = None) -> Iterator[Dict[str, Any]]:
    """
    Generate stream of gamepad state.

    Args:
        config: Optional configuration (uses defaults if None)

    Yields:
        Dict: Stream items with gamepad state

    Example:
        >>> for state in gamepad_stream():
        ...     # Map left stick to pitch/volume
        ...     pitch_control = state['left_stick_x']
        ...     volume_control = (state['left_stick_y'] + 1.0) / 2.0
        ...     if state['button_states'].get('button_0'):
        ...         print("Button A pressed!")
    """
    if config is None:
        config = GamepadConfig()

    state = GamepadStreamState(config)
    limiter = RateLimiter(config.rate_hz)

    try:
        while True:
            limiter.wait()
            yield state.poll()
    finally:
        state.close()
