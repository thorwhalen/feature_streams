"""
Pre-built transformers for stream processing.

This module provides common transformation functions for mapping between
different value ranges, musical scales, and control parameters.
"""

import math
from typing import List, Tuple


# ============================================================================
# Value Mapping Functions
# ============================================================================

def linear_map(
    value: float,
    in_range: Tuple[float, float],
    out_range: Tuple[float, float]
) -> float:
    """
    Map value from input range to output range linearly.

    Args:
        value: Input value
        in_range: (min, max) of input range
        out_range: (min, max) of output range

    Returns:
        float: Mapped value

    Example:
        >>> linear_map(0.5, (0, 1), (200, 800))
        500.0
    """
    in_min, in_max = in_range
    out_min, out_max = out_range

    # Normalize to [0, 1]
    if in_max == in_min:
        normalized = 0.5
    else:
        normalized = (value - in_min) / (in_max - in_min)

    # Map to output range
    return out_min + normalized * (out_max - out_min)


def exponential_map(
    value: float,
    in_range: Tuple[float, float],
    out_range: Tuple[float, float],
    curve: float = 2.0
) -> float:
    """
    Map value with exponential curve for more natural control.

    Args:
        value: Input value
        in_range: (min, max) of input range
        out_range: (min, max) of output range
        curve: Exponential curve factor (>1 = exponential, <1 = logarithmic)

    Returns:
        float: Mapped value

    Example:
        >>> # Exponential curve makes lower values change slower
        >>> exponential_map(0.5, (0, 1), (0, 100), curve=2.0)
        25.0
    """
    in_min, in_max = in_range
    out_min, out_max = out_range

    # Normalize to [0, 1]
    if in_max == in_min:
        normalized = 0.5
    else:
        normalized = (value - in_min) / (in_max - in_min)

    # Apply curve
    curved = normalized ** curve

    # Map to output range
    return out_min + curved * (out_max - out_min)


def quantize(value: float, steps: int, in_range: Tuple[float, float] = (0, 1)) -> float:
    """
    Quantize continuous value to discrete steps.

    Args:
        value: Input value
        steps: Number of discrete steps
        in_range: (min, max) of input range

    Returns:
        float: Quantized value

    Example:
        >>> quantize(0.37, 4, (0, 1))  # 4 steps: 0, 0.333, 0.667, 1.0
        0.333...
    """
    in_min, in_max = in_range

    # Normalize to [0, 1]
    if in_max == in_min:
        normalized = 0.5
    else:
        normalized = (value - in_min) / (in_max - in_min)

    # Quantize
    step_size = 1.0 / (steps - 1) if steps > 1 else 1.0
    step = round(normalized / step_size)
    quantized = step * step_size

    # Map back to original range
    return in_min + quantized * (in_max - in_min)


def smooth(value: float, prev_value: float, alpha: float = 0.1) -> float:
    """
    Smooth value using exponential moving average.

    Args:
        value: Current value
        prev_value: Previous smoothed value
        alpha: Smoothing factor [0, 1] (higher = less smoothing)

    Returns:
        float: Smoothed value

    Example:
        >>> smooth(1.0, 0.0, alpha=0.3)  # 30% new, 70% old
        0.3
    """
    return prev_value + alpha * (value - prev_value)


# ============================================================================
# Musical Transformations
# ============================================================================

def midi_to_freq(midi_note: int) -> float:
    """
    Convert MIDI note number to frequency in Hz.

    Args:
        midi_note: MIDI note number (0-127, 69 = A4 = 440Hz)

    Returns:
        float: Frequency in Hz

    Example:
        >>> midi_to_freq(69)  # A4
        440.0
        >>> midi_to_freq(60)  # Middle C
        261.63...
    """
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def freq_to_midi(freq: float) -> int:
    """
    Convert frequency to nearest MIDI note number.

    Args:
        freq: Frequency in Hz

    Returns:
        int: MIDI note number (0-127)

    Example:
        >>> freq_to_midi(440.0)
        69
        >>> freq_to_midi(261.63)
        60
    """
    if freq <= 0:
        return 0
    midi = 69 + 12 * math.log2(freq / 440.0)
    return int(round(max(0, min(127, midi))))


def quantize_to_scale(
    freq: float,
    scale: List[int],
    root: int = 60
) -> float:
    """
    Quantize frequency to nearest note in musical scale.

    Args:
        freq: Input frequency in Hz
        scale: List of scale intervals (e.g., [0, 2, 4, 5, 7, 9, 11] for major)
        root: Root MIDI note (default 60 = Middle C)

    Returns:
        float: Quantized frequency

    Example:
        >>> # Quantize to C major scale
        >>> quantize_to_scale(450.0, [0, 2, 4, 5, 7, 9, 11], root=60)
        # Returns frequency of nearest C major note
    """
    # Convert to MIDI
    midi = freq_to_midi(freq)

    # Find nearest scale note
    octave = (midi - root) // 12
    note_in_octave = (midi - root) % 12

    # Find closest scale degree
    closest_degree = min(scale, key=lambda x: abs(x - note_in_octave))

    # Construct quantized MIDI note
    quantized_midi = root + octave * 12 + closest_degree

    # Convert back to frequency
    return midi_to_freq(quantized_midi)


def velocity_curve(
    value: float,
    curve_type: str = 'linear',
    min_velocity: int = 1,
    max_velocity: int = 127
) -> int:
    """
    Apply velocity curve to input value.

    Args:
        value: Input value [0, 1]
        curve_type: 'linear', 'exponential', 'logarithmic'
        min_velocity: Minimum MIDI velocity
        max_velocity: Maximum MIDI velocity

    Returns:
        int: MIDI velocity (1-127)

    Example:
        >>> velocity_curve(0.5, 'linear')
        64
        >>> velocity_curve(0.5, 'exponential')
        32
    """
    value = max(0.0, min(1.0, value))

    if curve_type == 'linear':
        curved = value
    elif curve_type == 'exponential':
        curved = value ** 2
    elif curve_type == 'logarithmic':
        curved = math.sqrt(value)
    else:
        curved = value

    velocity = int(min_velocity + curved * (max_velocity - min_velocity))
    return max(1, min(127, velocity))


# ============================================================================
# Common Scales
# ============================================================================

# Scale intervals (semitones from root)
SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],
    'blues': [0, 3, 5, 6, 7, 10],
    'chromatic': list(range(12)),
    'whole_tone': [0, 2, 4, 6, 8, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
}


def get_scale(scale_name: str) -> List[int]:
    """
    Get scale intervals by name.

    Args:
        scale_name: Name of scale (see SCALES dict)

    Returns:
        list: Scale intervals in semitones

    Example:
        >>> get_scale('major')
        [0, 2, 4, 5, 7, 9, 11]
    """
    return SCALES.get(scale_name, SCALES['major'])


# ============================================================================
# Polar/Cartesian Conversions
# ============================================================================

def cartesian_to_polar(x: float, y: float) -> Tuple[float, float]:
    """
    Convert Cartesian (x, y) to polar (radius, angle).

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        tuple: (radius, angle_radians)

    Example:
        >>> r, theta = cartesian_to_polar(1.0, 1.0)
        >>> # r ≈ 1.414, theta ≈ 0.785 (45 degrees)
    """
    radius = math.sqrt(x**2 + y**2)
    angle = math.atan2(y, x)
    return radius, angle


def polar_to_cartesian(radius: float, angle: float) -> Tuple[float, float]:
    """
    Convert polar (radius, angle) to Cartesian (x, y).

    Args:
        radius: Radius
        angle: Angle in radians

    Returns:
        tuple: (x, y)

    Example:
        >>> x, y = polar_to_cartesian(1.0, math.pi/4)
        >>> # x ≈ 0.707, y ≈ 0.707
    """
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    return x, y


# ============================================================================
# dB Conversions
# ============================================================================

def linear_to_db(linear: float, min_db: float = -60.0) -> float:
    """
    Convert linear amplitude to decibels.

    Args:
        linear: Linear amplitude [0, 1]
        min_db: Minimum dB (for zero)

    Returns:
        float: dB value

    Example:
        >>> linear_to_db(1.0)
        0.0
        >>> linear_to_db(0.5)
        -6.02...
    """
    if linear <= 0:
        return min_db
    return 20 * math.log10(linear)


def db_to_linear(db: float) -> float:
    """
    Convert decibels to linear amplitude.

    Args:
        db: dB value

    Returns:
        float: Linear amplitude

    Example:
        >>> db_to_linear(0.0)
        1.0
        >>> db_to_linear(-6.0)
        0.501...
    """
    return 10 ** (db / 20.0)
