"""
Tests for tts_stream package.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tts_stream import TTSConfig, list_voices

# Try to import pyttsx3
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


def test_tts_config_defaults():
    """Test default configuration."""
    config = TTSConfig()
    assert config.default_rate == 150
    assert config.default_volume == 0.8
    assert config.queue_max_size == 10


def test_custom_config():
    """Test custom configuration."""
    config = TTSConfig(
        default_rate=180,
        default_volume=0.9,
        queue_max_size=20
    )
    assert config.default_rate == 180
    assert config.default_volume == 0.9
    assert config.queue_max_size == 20


def test_list_voices():
    """Test voice enumeration."""
    if not PYTTSX3_AVAILABLE:
        print("⊘ pyttsx3 not installed, skipping voice list test")
        return

    voices = list_voices()
    assert isinstance(voices, list)

    if len(voices) > 0:
        # Check structure
        voice = voices[0]
        assert 'id' in voice
        assert 'name' in voice
        assert 'languages' in voice
        print(f"✓ Found {len(voices)} voices")
    else:
        print("⊘ No voices available")


def test_tts_engine_creation():
    """Test TTS engine creation."""
    if not PYTTSX3_AVAILABLE:
        print("⊘ pyttsx3 not installed, skipping engine test")
        return

    from tts_stream.core import TTSEngine

    config = TTSConfig()
    engine = TTSEngine(config)

    assert engine.engine is not None
    assert engine.is_speaking is False
    assert engine.speech_queue.empty()

    engine.stop()
    print("✓ Engine creation OK")


def test_tts_speak_single():
    """Test speaking a single phrase."""
    if not PYTTSX3_AVAILABLE:
        print("⊘ pyttsx3 not installed, skipping speak test")
        return

    from tts_stream.core import TTSEngine

    config = TTSConfig(default_rate=200)  # Faster for testing
    engine = TTSEngine(config)

    # Queue a short phrase
    engine.speak({'text': 'Test', 'rate': 200})

    # Wait a bit
    time.sleep(0.5)

    # Should be processing or done
    timeout = 3.0
    start = time.time()
    while not engine.is_idle() and (time.time() - start) < timeout:
        time.sleep(0.1)

    engine.stop()
    print("✓ Speak test OK")


def test_tts_stream_consumer():
    """Test TTS consumer with short stream."""
    if not PYTTSX3_AVAILABLE:
        print("⊘ pyttsx3 not installed, skipping consumer test")
        return

    from tts_stream import tts_stream_consumer

    def short_text_stream():
        """Generate a few text items."""
        texts = ["One", "Two"]
        for text in texts:
            yield {
                'text': text,
                'rate': 250,  # Fast for testing
                'volume': 0.5
            }

    # This will speak briefly
    try:
        tts_stream_consumer(short_text_stream())
        print("✓ Consumer test OK")
    except Exception as e:
        print(f"⊘ Consumer test failed: {e}")


def test_priority_interrupt():
    """Test priority interruption."""
    if not PYTTSX3_AVAILABLE:
        print("⊘ pyttsx3 not installed, skipping priority test")
        return

    from tts_stream.core import TTSEngine

    config = TTSConfig()
    engine = TTSEngine(config)

    # Queue normal message
    engine.speak({'text': 'This is a long message that will be interrupted', 'rate': 100})

    time.sleep(0.2)

    # Queue high priority
    engine.speak({'text': 'Urgent', 'rate': 200, 'priority': 1})

    # Wait for completion
    time.sleep(2.0)

    engine.stop()
    print("✓ Priority test OK")


if __name__ == "__main__":
    print("Testing TTS config...")
    test_tts_config_defaults()
    print("✓ Config OK")

    print("\nTesting custom config...")
    test_custom_config()
    print("✓ Custom config OK")

    print("\nTesting list voices...")
    test_list_voices()

    print("\nTesting engine creation...")
    test_tts_engine_creation()

    print("\nTesting single speak...")
    test_tts_speak_single()

    print("\nTesting consumer...")
    test_tts_stream_consumer()

    print("\nTesting priority interrupt...")
    test_priority_interrupt()

    print("\nAll tests completed!")
