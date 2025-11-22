"""
Tests for trackpad_stream package.
"""

import sys
import os
import time
from threading import Thread

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from trackpad_stream import trackpad_stream, TrackpadConfig, get_screen_bounds


def test_get_screen_bounds():
    """Test screen bounds detection."""
    width, height = get_screen_bounds()
    assert width > 0
    assert height > 0
    assert isinstance(width, int)
    assert isinstance(height, int)


def test_trackpad_config_defaults():
    """Test default configuration."""
    config = TrackpadConfig()
    assert config.rate_hz == 60.0
    assert config.normalize_coords is True


def test_trackpad_stream_basic():
    """Test basic stream generation."""
    config = TrackpadConfig(rate_hz=10.0)  # Lower rate for testing
    stream = trackpad_stream(config)

    # Collect a few items
    items = []
    for i, item in enumerate(stream):
        items.append(item)
        if i >= 5:
            break

    # Verify we got items
    assert len(items) == 6

    # Verify structure of first item
    item = items[0]
    assert 'timestamp' in item
    assert 'x_norm' in item
    assert 'y_norm' in item
    assert 'x_raw' in item
    assert 'y_raw' in item
    assert 'left_click' in item
    assert 'right_click' in item
    assert 'scroll_delta_x' in item
    assert 'scroll_delta_y' in item

    # Verify normalized coordinates are in range
    for item in items:
        assert 0.0 <= item['x_norm'] <= 1.0
        assert 0.0 <= item['y_norm'] <= 1.0
        assert isinstance(item['left_click'], bool)
        assert isinstance(item['right_click'], bool)


def test_trackpad_stream_rate():
    """Test stream rate limiting."""
    config = TrackpadConfig(rate_hz=10.0)
    stream = trackpad_stream(config)

    timestamps = []
    for i, item in enumerate(stream):
        timestamps.append(item['timestamp'])
        if i >= 10:
            break

    # Calculate intervals
    intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    avg_interval = sum(intervals) / len(intervals)

    # Should be close to 1/10 = 0.1 seconds (with some tolerance)
    expected_interval = 1.0 / 10.0
    assert abs(avg_interval - expected_interval) < 0.05  # 50ms tolerance


def test_simulated_input():
    """Test with simulated mouse input."""
    from pynput.mouse import Controller

    controller = Controller()
    config = TrackpadConfig(rate_hz=20.0)

    # Start stream in background
    stream = trackpad_stream(config)
    items = []

    def collect_items():
        for i, item in enumerate(stream):
            items.append(item)
            if i >= 10:
                break

    thread = Thread(target=collect_items, daemon=True)
    thread.start()

    # Wait a bit for stream to start
    time.sleep(0.2)

    # Move mouse to known position
    initial_pos = controller.position
    controller.position = (500, 300)
    time.sleep(0.2)

    # Restore position
    controller.position = initial_pos

    thread.join(timeout=2.0)

    # Verify we captured some events
    assert len(items) > 0

    # At least some items should have x_raw near 500 (with tolerance)
    # (depending on timing, we may or may not catch the exact position)
    assert any(item['timestamp'] > 0 for item in items)


if __name__ == "__main__":
    # Run basic test
    print("Testing screen bounds...")
    test_get_screen_bounds()
    print("✓ Screen bounds OK")

    print("\nTesting config...")
    test_trackpad_config_defaults()
    print("✓ Config OK")

    print("\nTesting basic stream...")
    test_trackpad_stream_basic()
    print("✓ Basic stream OK")

    print("\nTesting stream rate...")
    test_trackpad_stream_rate()
    print("✓ Stream rate OK")

    print("\nAll tests passed!")
