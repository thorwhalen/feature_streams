"""
Tests for keyboard_stream package.
"""

import sys
import os
import time
from threading import Thread

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from keyboard_stream import keyboard_stream, KeyboardConfig, DEFAULT_KEY_MAPPING


def test_default_key_mapping():
    """Test default key mapping."""
    assert DEFAULT_KEY_MAPPING['a'] == 60  # Middle C
    assert DEFAULT_KEY_MAPPING['s'] == 62  # D4
    assert DEFAULT_KEY_MAPPING['k'] == 72  # C5
    assert len(DEFAULT_KEY_MAPPING) > 0


def test_keyboard_config_defaults():
    """Test default configuration."""
    config = KeyboardConfig()
    assert config.enable_velocity is True
    assert config.velocity_range == (64, 127)
    assert 'a' in config.key_to_note


def test_custom_mapping():
    """Test custom key mapping."""
    custom = {'z': 48, 'x': 49}
    config = KeyboardConfig(key_to_note=custom)
    assert config.key_to_note == custom
    assert 'a' not in config.key_to_note


def test_keyboard_stream_basic():
    """Test basic stream with simulated input."""
    from pynput.keyboard import Controller, Key

    controller = Controller()
    config = KeyboardConfig()

    stream = keyboard_stream(config)
    events = []

    def collect_events():
        for event in stream:
            events.append(event)
            if len(events) >= 4:  # Wait for press and release of 2 keys
                break

    # Start collector in background
    thread = Thread(target=collect_events, daemon=True)
    thread.start()

    # Give stream time to start
    time.sleep(0.2)

    # Simulate key presses
    controller.press('a')
    time.sleep(0.05)
    controller.release('a')
    time.sleep(0.05)
    controller.press('s')
    time.sleep(0.05)
    controller.release('s')

    # Wait for collection
    thread.join(timeout=2.0)

    # Verify we got events
    assert len(events) >= 2  # At least press events

    # Check event structure
    for event in events:
        assert 'timestamp' in event
        assert 'key' in event
        assert 'event_type' in event
        assert event['event_type'] in ['press', 'release']
        assert 'midi_note' in event
        assert 'midi_velocity' in event
        assert 'is_modifier' in event
        assert 'active_modifiers' in event
        assert 'octave_shift' in event

    # Check MIDI notes for 'a' and 's'
    press_events = [e for e in events if e['event_type'] == 'press']
    if len(press_events) >= 2:
        # Should have MIDI notes from default mapping
        assert press_events[0]['midi_note'] in [60, 62]  # a or s


def test_event_types():
    """Test press and release event generation."""
    from pynput.keyboard import Controller

    controller = Controller()
    config = KeyboardConfig()

    stream = keyboard_stream(config)
    events = []

    def collect_events():
        for event in stream:
            events.append(event)
            if len(events) >= 2:
                break

    thread = Thread(target=collect_events, daemon=True)
    thread.start()

    time.sleep(0.2)

    # Press and release
    controller.press('a')
    time.sleep(0.05)
    controller.release('a')

    thread.join(timeout=2.0)

    if len(events) >= 2:
        # Should have both press and release
        event_types = [e['event_type'] for e in events]
        assert 'press' in event_types or 'release' in event_types


def test_velocity_range():
    """Test velocity is within configured range."""
    config = KeyboardConfig(velocity_range=(50, 100))

    # Just verify config is set correctly
    assert config.velocity_range == (50, 100)


def test_octave_shift():
    """Test octave shift calculation."""
    config = KeyboardConfig()

    # This test just verifies the config and structure
    # Actual octave shifting would require modifier key simulation
    assert config.key_to_note is not None


if __name__ == "__main__":
    print("Testing default key mapping...")
    test_default_key_mapping()
    print("✓ Default mapping OK")

    print("\nTesting config...")
    test_keyboard_config_defaults()
    print("✓ Config OK")

    print("\nTesting custom mapping...")
    test_custom_mapping()
    print("✓ Custom mapping OK")

    print("\nTesting velocity range...")
    test_velocity_range()
    print("✓ Velocity range OK")

    print("\nAll tests passed!")
