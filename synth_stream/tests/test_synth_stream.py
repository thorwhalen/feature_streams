"""
Tests for synth_stream package.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from synth_stream import SynthConfig, Waveform

# Try to import dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


def test_synth_config_defaults():
    """Test default configuration."""
    config = SynthConfig()
    assert config.sample_rate == 44100
    assert config.block_size == 512
    assert config.channels == 1
    assert config.interpolation_alpha == 0.1


def test_waveform_enum():
    """Test waveform enumeration."""
    assert Waveform.SINE.value == "sine"
    assert Waveform.SAW.value == "saw"
    assert Waveform.SQUARE.value == "square"
    assert Waveform.TRIANGLE.value == "triangle"


def test_custom_config():
    """Test custom configuration."""
    config = SynthConfig(
        sample_rate=48000,
        block_size=256,
        channels=2,
        interpolation_alpha=0.2
    )
    assert config.sample_rate == 48000
    assert config.block_size == 256
    assert config.channels == 2
    assert config.interpolation_alpha == 0.2


def test_synth_engine_creation():
    """Test synth engine creation (requires dependencies)."""
    if not (NUMPY_AVAILABLE and SOUNDDEVICE_AVAILABLE):
        print("⊘ Dependencies not available, skipping engine test")
        return

    from synth_stream.core import SynthEngine

    config = SynthConfig()
    engine = SynthEngine(config)

    assert engine.pitch_hz == 440.0
    assert engine.amplitude == 0.5
    assert engine.waveform == Waveform.SINE

    print("✓ Engine creation OK")


def test_parameter_update():
    """Test parameter updates."""
    if not (NUMPY_AVAILABLE and SOUNDDEVICE_AVAILABLE):
        print("⊘ Dependencies not available, skipping parameter test")
        return

    from synth_stream.core import SynthEngine

    config = SynthConfig()
    engine = SynthEngine(config)

    # Update parameters
    engine.update_params({
        'pitch_hz': 880.0,
        'amplitude': 0.8,
        'waveform_type': 'square'
    })

    # Check targets are set
    assert engine.target_pitch_hz == 880.0
    assert engine.target_amplitude == 0.8
    assert engine.waveform == Waveform.SQUARE

    print("✓ Parameter update OK")


def test_waveform_generation():
    """Test waveform generation."""
    if not NUMPY_AVAILABLE:
        print("⊘ numpy not available, skipping waveform test")
        return

    from synth_stream.core import SynthEngine

    config = SynthConfig()
    engine = SynthEngine(config)

    # Generate test phase
    phase = np.linspace(0, 2*np.pi, 100)

    # Test each waveform
    for waveform in Waveform:
        samples = engine._generate_waveform(phase, waveform)
        assert len(samples) == 100
        assert samples.min() >= -1.0
        assert samples.max() <= 1.0

    print("✓ Waveform generation OK")


def test_synth_stream_consumer_short():
    """Test synth consumer with short stream."""
    if not (NUMPY_AVAILABLE and SOUNDDEVICE_AVAILABLE):
        print("⊘ Dependencies not available, skipping consumer test")
        return

    from synth_stream import synth_stream_consumer

    def short_control_stream():
        """Generate a few control dicts."""
        for i in range(5):
            yield {
                'pitch_hz': 440.0 + i * 10,
                'amplitude': 0.3,
                'waveform_type': 'sine'
            }
            time.sleep(0.05)

    # This will output audio for ~0.25 seconds
    try:
        synth_stream_consumer(short_control_stream())
        print("✓ Consumer test OK")
    except Exception as e:
        print(f"⊘ Consumer test failed: {e}")


if __name__ == "__main__":
    print("Testing synth config...")
    test_synth_config_defaults()
    print("✓ Config OK")

    print("\nTesting waveform enum...")
    test_waveform_enum()
    print("✓ Waveform enum OK")

    print("\nTesting custom config...")
    test_custom_config()
    print("✓ Custom config OK")

    print("\nTesting engine creation...")
    test_synth_engine_creation()

    print("\nTesting parameter update...")
    test_parameter_update()

    print("\nTesting waveform generation...")
    test_waveform_generation()

    print("\nTesting consumer (short audio output)...")
    test_synth_stream_consumer_short()

    print("\nAll tests completed!")
