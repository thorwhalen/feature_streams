"""
Core implementation for audio input stream with feature extraction.
"""

import sys
import os
from typing import Iterator, Dict, Any, Optional, List
from dataclasses import dataclass
import warnings
import math

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp

# Import audio dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    warnings.warn("numpy not installed. Install with: pip install numpy")

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    warnings.warn("sounddevice not installed. Install with: pip install sounddevice")

try:
    import aubio
    AUBIO_AVAILABLE = True
except ImportError:
    AUBIO_AVAILABLE = False
    warnings.warn("aubio not installed (optional). Install with: pip install aubio")


@dataclass
class AudioInputConfig:
    """Configuration for audio input stream."""
    sample_rate: int = 44100
    block_size: int = 2048
    hop_size: int = 512
    device: Optional[int] = None  # None = default input device
    channels: int = 1  # Mono input


def list_audio_devices() -> List[Dict[str, Any]]:
    """
    List available audio input devices.

    Returns:
        List of dicts with device info
    """
    if not SOUNDDEVICE_AVAILABLE:
        return []

    devices = sd.query_devices()
    result = []

    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            result.append({
                'id': i,
                'name': device['name'],
                'channels': device['max_input_channels'],
                'sample_rate': device['default_samplerate']
            })

    return result


class AudioFeatureExtractor:
    """Extract musical features from audio."""

    def __init__(self, config: AudioInputConfig):
        if not NUMPY_AVAILABLE or not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("numpy and sounddevice required")

        self.config = config
        self.use_aubio = AUBIO_AVAILABLE

        if self.use_aubio:
            # Initialize aubio pitch detector
            self.pitch_detector = aubio.pitch(
                "default", config.block_size, config.hop_size, config.sample_rate
            )
            self.pitch_detector.set_unit("Hz")
            self.pitch_detector.set_silence(-40)  # Silence threshold in dB
        else:
            warnings.warn("aubio not available, pitch detection will be basic")

    def _compute_rms(self, audio_block: np.ndarray) -> float:
        """Compute RMS energy of audio block."""
        return float(np.sqrt(np.mean(audio_block ** 2)))

    def _rms_to_db(self, rms: float) -> float:
        """Convert RMS to decibels."""
        if rms < 1e-10:
            return -100.0
        return 20 * math.log10(rms)

    def _compute_spectral_centroid(self, audio_block: np.ndarray) -> float:
        """Compute spectral centroid (brightness measure)."""
        # Compute FFT
        spectrum = np.abs(np.fft.rfft(audio_block))
        freqs = np.fft.rfftfreq(len(audio_block), 1.0 / self.config.sample_rate)

        # Weighted average of frequencies
        if np.sum(spectrum) > 0:
            centroid = np.sum(freqs * spectrum) / np.sum(spectrum)
        else:
            centroid = 0.0

        return float(centroid)

    def _detect_pitch_aubio(self, audio_block: np.ndarray) -> tuple:
        """Detect pitch using aubio."""
        pitch = self.pitch_detector(audio_block.astype(np.float32))[0]
        confidence = self.pitch_detector.get_confidence()
        return float(pitch), float(confidence)

    def _detect_pitch_basic(self, audio_block: np.ndarray) -> tuple:
        """Basic pitch detection using autocorrelation."""
        # Simple autocorrelation-based pitch detection
        autocorr = np.correlate(audio_block, audio_block, mode='full')
        autocorr = autocorr[len(autocorr)//2:]

        # Find first peak after zero lag
        min_period = int(self.config.sample_rate / 1000)  # 1000 Hz max
        max_period = int(self.config.sample_rate / 50)    # 50 Hz min

        if len(autocorr) > max_period:
            autocorr_range = autocorr[min_period:max_period]
            if len(autocorr_range) > 0:
                peak = np.argmax(autocorr_range) + min_period
                pitch = self.config.sample_rate / peak
                confidence = float(autocorr_range[peak - min_period] / autocorr[0])
                return float(pitch), max(0.0, min(1.0, confidence))

        return 0.0, 0.0

    def extract_features(self, audio_block: np.ndarray) -> Dict[str, Any]:
        """
        Extract features from audio block.

        Args:
            audio_block: Audio samples (1D numpy array)

        Returns:
            Dict with extracted features
        """
        # Compute RMS and loudness
        rms = self._compute_rms(audio_block)
        loudness_db = self._rms_to_db(rms)

        # Detect pitch
        if self.use_aubio:
            pitch_hz, confidence = self._detect_pitch_aubio(audio_block)
        else:
            pitch_hz, confidence = self._detect_pitch_basic(audio_block)

        # Compute spectral centroid
        spectral_centroid = self._compute_spectral_centroid(audio_block)

        # Normalize spectral centroid to [0, 1] (assuming 0-8000 Hz range)
        spectral_centroid_norm = min(1.0, spectral_centroid / 8000.0)

        # Determine if voiced (pitch detected with confidence)
        is_voiced = pitch_hz > 50 and confidence > 0.5

        return {
            'timestamp': timestamp(),
            'pitch_hz': pitch_hz,
            'pitch_confidence': confidence,
            'loudness_db': loudness_db,
            'loudness_norm': max(0.0, min(1.0, (loudness_db + 60) / 60)),  # -60dB to 0dB → 0 to 1
            'spectral_centroid_hz': spectral_centroid,
            'spectral_centroid_norm': spectral_centroid_norm,
            'is_voiced': is_voiced,
            'rms': rms,
        }


def audio_input_stream(config: Optional[AudioInputConfig] = None) -> Iterator[Dict[str, Any]]:
    """
    Generate stream of audio features from microphone input.

    Args:
        config: Optional configuration (uses defaults if None)

    Yields:
        Dict: Stream items with audio features

    Example:
        >>> for features in audio_input_stream():
        ...     if features['is_voiced']:
        ...         print(f"Pitch: {features['pitch_hz']:.1f} Hz")
    """
    if config is None:
        config = AudioInputConfig()

    extractor = AudioFeatureExtractor(config)

    # Audio buffer for accumulating samples
    audio_buffer = np.zeros(config.block_size, dtype=np.float32)
    buffer_pos = 0

    def audio_callback(indata, frames, time_info, status):
        nonlocal buffer_pos

        if status:
            warnings.warn(f"Audio input status: {status}")

        # Get mono audio
        if config.channels == 1:
            mono = indata[:, 0]
        else:
            mono = np.mean(indata, axis=1)

        # Add to buffer
        samples_to_copy = min(frames, config.block_size - buffer_pos)
        audio_buffer[buffer_pos:buffer_pos + samples_to_copy] = mono[:samples_to_copy]
        buffer_pos += samples_to_copy

    # Start audio stream
    stream = sd.InputStream(
        samplerate=config.sample_rate,
        blocksize=config.hop_size,
        channels=config.channels,
        device=config.device,
        callback=audio_callback
    )

    stream.start()

    try:
        while True:
            # Wait for buffer to fill
            if buffer_pos >= config.block_size:
                # Extract features
                features = extractor.extract_features(audio_buffer.copy())

                # Shift buffer (overlap)
                shift = config.hop_size
                audio_buffer[:-shift] = audio_buffer[shift:]
                buffer_pos -= shift

                yield features
            else:
                # Wait a bit for more data
                import time
                time.sleep(config.hop_size / config.sample_rate)

    finally:
        stream.stop()
        stream.close()
