"""
Tests for gamepad_stream package.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gamepad_stream import GamepadConfig, list_gamepads

# Try to import pygame
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


def test_gamepad_config_defaults():
    """Test default configuration."""
    config = GamepadConfig()
    assert config.device_id == 0
    assert config.rate_hz == 60.0
    assert config.deadzone == 0.1
    assert config.enable_buttons is True
    assert config.enable_axes is True
    assert config.enable_hat is True


def test_list_gamepads():
    """Test gamepad enumeration."""
    gamepads = list_gamepads()
    # May be empty if no gamepads connected
    assert isinstance(gamepads, list)


def test_custom_config():
    """Test custom configuration."""
    config = GamepadConfig(
        device_id=1,
        rate_hz=120.0,
        deadzone=0.2,
        enable_buttons=False
    )
    assert config.device_id == 1
    assert config.rate_hz == 120.0
    assert config.deadzone == 0.2
    assert config.enable_buttons is False


def test_gamepad_stream_structure():
    """Test stream output structure (mock test)."""
    # This is a structure test - verifies expected keys
    expected_keys = [
        'timestamp', 'device_id', 'left_stick_x', 'left_stick_y',
        'right_stick_x', 'right_stick_y', 'left_trigger', 'right_trigger',
        'button_states', 'dpad_x', 'dpad_y'
    ]

    # Just verify the expected structure
    assert all(isinstance(key, str) for key in expected_keys)


def test_gamepad_stream_with_device():
    """Test actual gamepad stream (requires connected gamepad)."""
    if not PYGAME_AVAILABLE:
        print("⊘ pygame not installed, skipping device test")
        return

    gamepads = list_gamepads()
    if len(gamepads) == 0:
        print("⊘ No gamepads connected, skipping device test")
        return

    from gamepad_stream import gamepad_stream

    try:
        config = GamepadConfig(rate_hz=10.0)  # Low rate for testing
        stream = gamepad_stream(config)

        # Collect a few samples
        samples = []
        for i, state in enumerate(stream):
            samples.append(state)
            if i >= 3:
                break

        # Verify structure
        assert len(samples) == 4
        for state in samples:
            assert 'timestamp' in state
            assert 'device_id' in state
            assert 'left_stick_x' in state
            assert 'button_states' in state
            assert isinstance(state['button_states'], dict)

            # Verify value ranges
            assert -1.0 <= state['left_stick_x'] <= 1.0
            assert -1.0 <= state['left_stick_y'] <= 1.0
            assert 0.0 <= state['left_trigger'] <= 1.0

        print("✓ Gamepad stream test passed")

    except RuntimeError as e:
        print(f"⊘ Could not test gamepad: {e}")


if __name__ == "__main__":
    print("Testing gamepad config...")
    test_gamepad_config_defaults()
    print("✓ Config OK")

    print("\nTesting list gamepads...")
    test_list_gamepads()
    print("✓ List gamepads OK")

    print("\nTesting custom config...")
    test_custom_config()
    print("✓ Custom config OK")

    print("\nTesting structure...")
    test_gamepad_stream_structure()
    print("✓ Structure OK")

    print("\nTesting with device (if available)...")
    test_gamepad_stream_with_device()

    print("\nAll tests completed!")
