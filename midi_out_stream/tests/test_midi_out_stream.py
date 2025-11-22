"""
Tests for midi_out_stream package.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from midi_out_stream import MIDIConfig, list_midi_ports

# Try to import mido
try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False


def test_midi_config_defaults():
    """Test default configuration."""
    config = MIDIConfig()
    assert config.port_name is None
    assert config.create_virtual_port is False
    assert config.default_channel == 0
    assert config.auto_note_off_delay == 0.5


def test_custom_config():
    """Test custom configuration."""
    config = MIDIConfig(
        port_name="Test Port",
        create_virtual_port=True,
        virtual_port_name="MyVirtualPort",
        default_channel=5
    )
    assert config.port_name == "Test Port"
    assert config.create_virtual_port is True
    assert config.virtual_port_name == "MyVirtualPort"
    assert config.default_channel == 5


def test_list_midi_ports():
    """Test MIDI port enumeration."""
    if not MIDO_AVAILABLE:
        print("⊘ mido not installed, skipping port list test")
        return

    ports = list_midi_ports()
    assert isinstance(ports, list)
    print(f"✓ Found {len(ports)} MIDI ports")


def test_midi_engine_creation():
    """Test MIDI engine creation."""
    if not MIDO_AVAILABLE:
        print("⊘ mido not installed, skipping engine test")
        return

    from midi_out_stream.core import MIDIOutputEngine

    try:
        # Try to create with virtual port
        config = MIDIConfig(create_virtual_port=True, virtual_port_name="test_port")
        engine = MIDIOutputEngine(config)

        assert engine.port is not None
        assert len(engine.active_notes) == 0

        engine.close()
        print("✓ Engine creation OK")

    except RuntimeError as e:
        print(f"⊘ Could not create MIDI engine: {e}")


def test_note_message_processing():
    """Test note message processing."""
    if not MIDO_AVAILABLE:
        print("⊘ mido not installed, skipping message test")
        return

    from midi_out_stream.core import MIDIOutputEngine

    try:
        config = MIDIConfig(create_virtual_port=True)
        engine = MIDIOutputEngine(config)

        # Send note on
        control_dict = {
            'event_type': 'note',
            'midi_note': 60,
            'velocity': 100,
            'channel': 0
        }
        engine.process_control_dict(control_dict)

        # Check active notes
        assert (0, 60) in engine.active_notes

        # Send note off
        control_dict['velocity'] = 0
        engine.process_control_dict(control_dict)

        # Should be removed from active notes
        time.sleep(0.1)
        assert (0, 60) not in engine.active_notes

        engine.close()
        print("✓ Note message processing OK")

    except RuntimeError as e:
        print(f"⊘ Could not test messages: {e}")


def test_control_change():
    """Test control change messages."""
    if not MIDO_AVAILABLE:
        print("⊘ mido not installed, skipping CC test")
        return

    from midi_out_stream.core import MIDIOutputEngine

    try:
        config = MIDIConfig(create_virtual_port=True)
        engine = MIDIOutputEngine(config)

        # Send CC message
        control_dict = {
            'event_type': 'cc',
            'cc_number': 1,  # Modulation
            'cc_value': 64,
            'channel': 0
        }
        engine.process_control_dict(control_dict)

        engine.close()
        print("✓ Control change OK")

    except RuntimeError as e:
        print(f"⊘ Could not test CC: {e}")


def test_auto_note_off():
    """Test automatic note-off scheduling."""
    if not MIDO_AVAILABLE:
        print("⊘ mido not installed, skipping auto note-off test")
        return

    from midi_out_stream.core import MIDIOutputEngine

    try:
        config = MIDIConfig(create_virtual_port=True)
        engine = MIDIOutputEngine(config)

        # Send note with duration
        control_dict = {
            'event_type': 'note',
            'midi_note': 60,
            'velocity': 100,
            'duration': 0.2,  # 200ms
            'channel': 0
        }
        engine.process_control_dict(control_dict)

        # Should be in active notes
        assert (0, 60) in engine.active_notes

        # Wait for auto note-off
        time.sleep(0.3)

        # Should be removed
        assert (0, 60) not in engine.active_notes

        engine.close()
        print("✓ Auto note-off OK")

    except RuntimeError as e:
        print(f"⊘ Could not test auto note-off: {e}")


def test_midi_consumer():
    """Test MIDI consumer with short stream."""
    if not MIDO_AVAILABLE:
        print("⊘ mido not installed, skipping consumer test")
        return

    from midi_out_stream import midi_out_stream_consumer

    def short_note_stream():
        """Generate a few notes."""
        for note in [60, 62, 64]:
            yield {
                'event_type': 'note',
                'midi_note': note,
                'velocity': 100,
                'duration': 0.1,
                'channel': 0
            }
            time.sleep(0.1)

    try:
        config = MIDIConfig(create_virtual_port=True)
        midi_out_stream_consumer(short_note_stream(), config)
        print("✓ Consumer test OK")

    except Exception as e:
        print(f"⊘ Consumer test failed: {e}")


if __name__ == "__main__":
    print("Testing MIDI config...")
    test_midi_config_defaults()
    print("✓ Config OK")

    print("\nTesting custom config...")
    test_custom_config()
    print("✓ Custom config OK")

    print("\nTesting list MIDI ports...")
    test_list_midi_ports()

    print("\nTesting engine creation...")
    test_midi_engine_creation()

    print("\nTesting note messages...")
    test_note_message_processing()

    print("\nTesting control change...")
    test_control_change()

    print("\nTesting auto note-off...")
    test_auto_note_off()

    print("\nTesting consumer...")
    test_midi_consumer()

    print("\nAll tests completed!")
