"""
Core implementation for synthesis stream consumer.
"""

import sys
import os
from typing import Iterator, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from threading import Thread, Lock
import warnings
import math

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import interpolate_value

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


class Waveform(Enum):
    """Supported waveform types."""
    SINE = "sine"
    SAW = "saw"
    SQUARE = "square"
    TRIANGLE = "triangle"


@dataclass
class SynthConfig:
    """Configuration for synthesizer."""
    sample_rate: int = 44100
    block_size: int = 512
    channels: int = 1  # Mono output
    device: Optional[int] = None  # None = default device
    interpolation_alpha: float = 0.1  # Smoothing factor for parameter changes


class SynthEngine:
    """Real-time synthesis engine."""

    def __init__(self, config: SynthConfig):
        if not NUMPY_AVAILABLE or not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("numpy and sounddevice required")

        self.config = config
        self.lock = Lock()

        # Current synthesis parameters
        self.pitch_hz = 440.0
        self.amplitude = 0.5
        self.waveform = Waveform.SINE
        self.filter_cutoff_hz = 5000.0

        # Target parameters (for interpolation)
        self.target_pitch_hz = 440.0
        self.target_amplitude = 0.5

        # Phase accumulator for oscillator
        self.phase = 0.0

        # Audio stream
        self.stream = None

    def _generate_waveform(self, phase: np.ndarray, waveform: Waveform) -> np.ndarray:
        """
        Generate waveform from phase.

        Args:
            phase: Phase values [0, 2π]
            waveform: Waveform type

        Returns:
            np.ndarray: Waveform samples [-1, 1]
        """
        if waveform == Waveform.SINE:
            return np.sin(phase)
        elif waveform == Waveform.SAW:
            # Sawtooth: ramp from -1 to 1
            return 2.0 * (phase / (2 * np.pi)) - 1.0
        elif waveform == Waveform.SQUARE:
            # Square wave
            return np.where(np.sin(phase) >= 0, 1.0, -1.0)
        elif waveform == Waveform.TRIANGLE:
            # Triangle wave
            saw = 2.0 * (phase / (2 * np.pi)) - 1.0
            return 2.0 * np.abs(saw) - 1.0
        else:
            return np.sin(phase)

    def _audio_callback(self, outdata, frames, time_info, status):
        """
        Audio callback for sounddevice.

        This is called in a separate thread by sounddevice.
        """
        if status:
            warnings.warn(f"Audio callback status: {status}")

        with self.lock:
            # Interpolate parameters for smooth transitions
            self.pitch_hz = interpolate_value(
                self.pitch_hz,
                self.target_pitch_hz,
                self.config.interpolation_alpha
            )
            self.amplitude = interpolate_value(
                self.amplitude,
                self.target_amplitude,
                self.config.interpolation_alpha
            )

            # Generate phase values
            phase_increment = 2 * np.pi * self.pitch_hz / self.config.sample_rate
            phases = self.phase + np.arange(frames) * phase_increment
            self.phase = (self.phase + frames * phase_increment) % (2 * np.pi)

            # Generate waveform
            samples = self._generate_waveform(phases, self.waveform)

            # Apply amplitude
            samples *= self.amplitude

            # Write to output
            if self.config.channels == 1:
                outdata[:, 0] = samples
            else:
                # Stereo: duplicate to both channels
                outdata[:, 0] = samples
                outdata[:, 1] = samples

    def update_params(self, control_dict: Dict[str, Any]):
        """
        Update synthesis parameters from control dict.

        Args:
            control_dict: Control parameters
        """
        with self.lock:
            if 'pitch_hz' in control_dict:
                self.target_pitch_hz = max(20.0, min(20000.0, control_dict['pitch_hz']))

            if 'amplitude' in control_dict:
                self.target_amplitude = max(0.0, min(1.0, control_dict['amplitude']))

            if 'waveform_type' in control_dict:
                waveform_str = control_dict['waveform_type'].lower()
                try:
                    self.waveform = Waveform(waveform_str)
                except ValueError:
                    pass  # Ignore invalid waveform

    def start(self):
        """Start audio output stream."""
        self.stream = sd.OutputStream(
            samplerate=self.config.sample_rate,
            blocksize=self.config.block_size,
            channels=self.config.channels,
            device=self.config.device,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop(self):
        """Stop audio output stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()


def synth_stream_consumer(
    control_stream: Iterator[Dict[str, Any]],
    config: Optional[SynthConfig] = None
):
    """
    Consume control stream and generate audio output.

    Args:
        control_stream: Iterator yielding control dictionaries
        config: Optional synthesis configuration

    Example:
        >>> def control_gen():
        ...     for i in range(100):
        ...         yield {'pitch_hz': 440 + i, 'amplitude': 0.5, 'waveform_type': 'sine'}
        ...         time.sleep(0.05)
        >>>
        >>> synth_stream_consumer(control_gen())
    """
    if config is None:
        config = SynthConfig()

    engine = SynthEngine(config)
    engine.start()

    try:
        for control_dict in control_stream:
            engine.update_params(control_dict)
    finally:
        engine.stop()
