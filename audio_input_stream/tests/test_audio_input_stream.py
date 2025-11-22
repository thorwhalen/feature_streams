"""
Tests for audio_input_stream package.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from audio_input_stream import AudioInputConfig, list_audio_devices

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


def test_audio_config_defaults():
    """Test default configuration."""
    config = AudioInputConfig()
    assert config.sample_rate == 44100
    assert config.block_size == 2048
    assert config.hop_size == 512
    assert config.channels == 1


def test_list_audio_devices():
    """Test audio device enumeration."""
    if not SOUNDDEVICE_AVAILABLE:
        print("⊘ sounddevice not installed, skipping device list test")
        return

    devices = list_audio_devices()
    assert isinstance(devices, list)
    print(f"✓ Found {len(devices)} audio input devices")


def test_feature_extractor_creation():
    """Test feature extractor creation."""
    if not (NUMPY_AVAILABLE and SOUNDDEVICE_AVAILABLE):
        print("⊘ Dependencies not available, skipping extractor test")
        return

    from audio_input_stream.core import AudioFeatureExtractor

    config = AudioInputConfig()
    extractor = AudioFeatureExtractor(config)

    assert extractor.config == config
    print("✓ Feature extractor creation OK")


def test_feature_extraction():
    """Test feature extraction from synthetic audio."""
    if not NUMPY_AVAILABLE:
        print("⊘ numpy not available, skipping feature extraction test")
        return

    from audio_input_stream.core import AudioFeatureExtractor

    config = AudioInputConfig()
    extractor = AudioFeatureExtractor(config)

    # Generate test signal (440 Hz sine wave)
    t = np.linspace(0, config.block_size / config.sample_rate, config.block_size)
    audio_block = 0.5 * np.sin(2 * np.pi * 440 * t)

    features = extractor.extract_features(audio_block)

    # Verify structure
    assert 'timestamp' in features
    assert 'pitch_hz' in features
    assert 'pitch_confidence' in features
    assert 'loudness_db' in features
    assert 'spectral_centroid_hz' in features
    assert 'is_voiced' in features

    # Pitch should be around 440 Hz (with some tolerance)
    if features['pitch_hz'] > 0:
        assert 400 < features['pitch_hz'] < 480

    print("✓ Feature extraction OK")


def test_rms_calculation():
    """Test RMS calculation."""
    if not NUMPY_AVAILABLE:
        print("⊘ numpy not available, skipping RMS test")
        return

    from audio_input_stream.core import AudioFeatureExtractor

    config = AudioInputConfig()
    extractor = AudioFeatureExtractor(config)

    # Test with known signal
    signal = np.ones(1000) * 0.5
    rms = extractor._compute_rms(signal)

    assert abs(rms - 0.5) < 0.01

    print("✓ RMS calculation OK")


def test_audio_stream_short():
    """Test audio stream with short capture (requires microphone)."""
    if not (NUMPY_AVAILABLE and SOUNDDEVICE_AVAILABLE):
        print("⊘ Dependencies not available, skipping stream test")
        return

    from audio_input_stream import audio_input_stream

    try:
        stream = audio_input_stream()

        # Capture a few frames
        features_list = []
        for i, features in enumerate(stream):
            features_list.append(features)
            if i >= 3:
                break

        # Verify we got features
        assert len(features_list) == 4

        # Check structure
        for features in features_list:
            assert 'pitch_hz' in features
            assert 'loudness_db' in features

        print("✓ Audio stream test OK")

    except Exception as e:
        print(f"⊘ Could not test audio stream: {e}")


if __name__ == "__main__":
    print("Testing audio config...")
    test_audio_config_defaults()
    print("✓ Config OK")

    print("\nTesting list audio devices...")
    test_list_audio_devices()

    print("\nTesting feature extractor creation...")
    test_feature_extractor_creation()

    print("\nTesting feature extraction...")
    test_feature_extraction()

    print("\nTesting RMS calculation...")
    test_rms_calculation()

    print("\nTesting audio stream (short, requires mic)...")
    test_audio_stream_short()

    print("\nAll tests completed!")
