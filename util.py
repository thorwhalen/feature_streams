"""
Shared utilities for feature_streams packages.

This module provides common functionality used across multiple stream packages,
including timestamping, normalization, and stream wrapper utilities.
"""

import time
from typing import Iterator, Dict, Any, Callable, Optional
from queue import Queue, Empty
from threading import Thread, Event
import warnings


def timestamp() -> float:
    """
    Get current Unix timestamp.

    Returns:
        float: Current time as Unix timestamp (seconds since epoch)
    """
    return time.time()


def normalize(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize a value to [0.0, 1.0] range.

    Args:
        value: Value to normalize
        min_val: Minimum value of input range
        max_val: Maximum value of input range

    Returns:
        float: Normalized value in [0.0, 1.0], clamped to bounds
    """
    if max_val == min_val:
        return 0.5  # Avoid division by zero
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))  # Clamp to [0, 1]


def apply_deadzone(value: float, deadzone: float = 0.1) -> float:
    """
    Apply dead-zone to analog input to prevent drift.

    Args:
        value: Input value in [-1.0, 1.0] range
        deadzone: Dead-zone threshold (default 0.1)

    Returns:
        float: Value with dead-zone applied, re-scaled to full range
    """
    if abs(value) < deadzone:
        return 0.0

    # Re-scale to full range outside dead-zone
    sign = 1 if value > 0 else -1
    scaled = (abs(value) - deadzone) / (1.0 - deadzone)
    return sign * min(1.0, scaled)


class StreamBuffer:
    """
    Thread-safe buffer for streaming data between producer and consumer.

    This class provides a queue-based buffer with timeout support,
    useful for decoupling event-driven inputs from continuous stream outputs.
    """

    def __init__(self, maxsize: int = 0):
        """
        Initialize stream buffer.

        Args:
            maxsize: Maximum queue size (0 = unlimited)
        """
        self.queue = Queue(maxsize=maxsize)
        self._stop_event = Event()

    def put(self, item: Any, timeout: Optional[float] = None) -> bool:
        """
        Put item into buffer.

        Args:
            item: Item to put in buffer
            timeout: Timeout in seconds (None = blocking)

        Returns:
            bool: True if successful, False if timeout/stopped
        """
        if self._stop_event.is_set():
            return False
        try:
            self.queue.put(item, timeout=timeout)
            return True
        except:
            return False

    def get(self, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Get item from buffer.

        Args:
            timeout: Timeout in seconds (None = blocking)

        Returns:
            Item from buffer, or None if timeout/stopped
        """
        try:
            return self.queue.get(timeout=timeout)
        except Empty:
            return None

    def stop(self):
        """Signal buffer to stop accepting/providing items."""
        self._stop_event.set()

    def is_stopped(self) -> bool:
        """Check if buffer is stopped."""
        return self._stop_event.is_set()


class RateLimiter:
    """
    Rate limiter for controlling stream output frequency.

    Ensures items are yielded at a maximum rate (Hz).
    """

    def __init__(self, rate_hz: float):
        """
        Initialize rate limiter.

        Args:
            rate_hz: Maximum rate in Hz (items per second)
        """
        self.interval = 1.0 / rate_hz
        self.last_time = 0.0

    def wait(self):
        """Wait until next item can be emitted based on rate limit."""
        current_time = time.time()
        elapsed = current_time - self.last_time
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_time = time.time()

    def should_emit(self) -> bool:
        """
        Check if enough time has passed to emit next item.

        Returns:
            bool: True if should emit now, False otherwise
        """
        current_time = time.time()
        return (current_time - self.last_time) >= self.interval

    def reset(self):
        """Reset the rate limiter timer."""
        self.last_time = time.time()


def stream_from_callback(
    callback_starter: Callable[[Callable], Any],
    rate_hz: float = 60.0,
    buffer_size: int = 100
) -> Iterator[Dict[str, Any]]:
    """
    Create a stream generator from callback-based API.

    Many input libraries (pynput, pygame events) use callbacks. This utility
    converts callback-based APIs into generator-based streams.

    Args:
        callback_starter: Function that starts callbacks, takes callback function as arg
        rate_hz: Stream output rate in Hz
        buffer_size: Internal buffer size

    Yields:
        Dict: Stream items from callbacks

    Example:
        >>> def start_callbacks(callback):
        ...     listener = SomeListener(on_event=callback)
        ...     listener.start()
        ...     return listener
        >>>
        >>> for item in stream_from_callback(start_callbacks):
        ...     print(item)
    """
    buffer = StreamBuffer(maxsize=buffer_size)
    limiter = RateLimiter(rate_hz)

    # Start callback handler
    handler = callback_starter(buffer.put)

    try:
        latest_item = None
        while not buffer.is_stopped():
            # Try to get latest item from buffer
            item = buffer.get(timeout=0.01)
            if item is not None:
                latest_item = item

            # Emit latest item at rate limit
            if limiter.should_emit() and latest_item is not None:
                yield latest_item
                limiter.reset()

    finally:
        buffer.stop()
        # Try to stop handler if it has a stop method
        if hasattr(handler, 'stop'):
            handler.stop()


def consume_stream(
    stream: Iterator[Dict[str, Any]],
    consumer: Callable[[Dict[str, Any]], None],
    stop_event: Optional[Event] = None
):
    """
    Consume a stream in a separate thread.

    Args:
        stream: Stream iterator to consume
        consumer: Function called for each stream item
        stop_event: Optional event to signal stop

    Returns:
        Thread: Started thread consuming the stream
    """
    def _consume():
        try:
            for item in stream:
                if stop_event and stop_event.is_set():
                    break
                consumer(item)
        except Exception as e:
            warnings.warn(f"Stream consumer error: {e}")

    thread = Thread(target=_consume, daemon=True)
    thread.start()
    return thread


def interpolate_value(current: float, target: float, alpha: float = 0.1) -> float:
    """
    Linearly interpolate between current and target value.

    Useful for smooth parameter transitions to avoid audio clicks/pops.

    Args:
        current: Current value
        target: Target value
        alpha: Interpolation factor [0.0, 1.0] (higher = faster transition)

    Returns:
        float: Interpolated value
    """
    return current + alpha * (target - current)


# ============================================================================
# Stream Recording and Playback
# ============================================================================

def record_stream(
    stream: Iterator[Dict[str, Any]],
    filepath: str,
    max_items: Optional[int] = None
):
    """
    Record stream to JSON lines file.

    Args:
        stream: Stream iterator to record
        filepath: Output file path (.jsonl extension recommended)
        max_items: Maximum items to record (None = unlimited)

    Example:
        >>> record_stream(trackpad_stream(), 'recording.jsonl', max_items=1000)
    """
    import json

    with open(filepath, 'w') as f:
        for i, item in enumerate(stream):
            if max_items and i >= max_items:
                break
            f.write(json.dumps(item) + '\n')


def playback_stream(
    filepath: str,
    realtime: bool = True,
    speed: float = 1.0
) -> Iterator[Dict[str, Any]]:
    """
    Replay stream from JSON lines file.

    Args:
        filepath: Input file path
        realtime: If True, replay at original timing (default)
        speed: Speed multiplier for realtime playback (2.0 = 2x speed)

    Yields:
        Dict: Stream items from file

    Example:
        >>> for item in playback_stream('recording.jsonl'):
        ...     print(item)
    """
    import json

    with open(filepath, 'r') as f:
        last_timestamp = None

        for line in f:
            item = json.loads(line.strip())

            if realtime and 'timestamp' in item:
                if last_timestamp is not None:
                    # Sleep for the time difference
                    delay = (item['timestamp'] - last_timestamp) / speed
                    if delay > 0:
                        time.sleep(delay)
                last_timestamp = item['timestamp']

            yield item


# ============================================================================
# Stream Composition Utilities
# ============================================================================

def merge_streams(
    *streams: Iterator[Dict[str, Any]],
    strategy: str = 'latest'
) -> Iterator[Dict[str, Any]]:
    """
    Merge multiple input streams into one.

    Args:
        *streams: Variable number of stream iterators
        strategy: Merge strategy ('latest', 'combine')
            - 'latest': Emit latest value from each stream
            - 'combine': Combine all stream dicts into one

    Yields:
        Dict: Merged stream items

    Example:
        >>> trackpad = trackpad_stream()
        >>> keyboard = keyboard_stream()
        >>> for item in merge_streams(trackpad, keyboard, strategy='combine'):
        ...     # item contains fields from both streams
        ...     pass
    """
    from threading import Thread
    from queue import Queue, Empty

    # Queue for each stream
    queues = [Queue(maxsize=10) for _ in streams]
    stop_event = Event()

    # Start thread for each stream
    def stream_reader(stream, queue):
        try:
            for item in stream:
                if stop_event.is_set():
                    break
                try:
                    queue.put(item, timeout=0.1)
                except:
                    pass  # Queue full, drop item
        except:
            pass

    threads = []
    for stream, queue in zip(streams, queues):
        thread = Thread(target=stream_reader, args=(stream, queue), daemon=True)
        thread.start()
        threads.append(thread)

    try:
        # Latest value from each stream
        latest_values = [None] * len(streams)

        while not stop_event.is_set():
            # Try to get from each queue
            for i, queue in enumerate(queues):
                try:
                    item = queue.get(timeout=0.01)
                    latest_values[i] = item
                except Empty:
                    pass

            # Emit merged result if we have at least one value
            if any(v is not None for v in latest_values):
                if strategy == 'latest':
                    # Yield the most recent update
                    for v in reversed(latest_values):
                        if v is not None:
                            yield v
                            break
                elif strategy == 'combine':
                    # Combine all dicts
                    merged = {'timestamp': timestamp()}
                    for v in latest_values:
                        if v is not None:
                            merged.update(v)
                    yield merged

                time.sleep(0.001)  # Small delay

    finally:
        stop_event.set()
        for thread in threads:
            thread.join(timeout=0.1)


def broadcast_stream(
    stream: Iterator[Dict[str, Any]],
    num_consumers: int = 2
) -> list:
    """
    Broadcast stream to multiple consumers efficiently.

    Better than itertools.tee for streams with side effects.

    Args:
        stream: Input stream
        num_consumers: Number of output streams

    Returns:
        list: List of output stream iterators

    Example:
        >>> input_stream = trackpad_stream()
        >>> stream1, stream2 = broadcast_stream(input_stream, 2)
        >>> # Use stream1 for synth, stream2 for MIDI
    """
    queues = [Queue(maxsize=100) for _ in range(num_consumers)]
    stop_event = Event()

    def reader_thread():
        try:
            for item in stream:
                if stop_event.is_set():
                    break
                # Send to all queues
                for queue in queues:
                    try:
                        queue.put(item, timeout=0.1)
                    except:
                        pass  # Queue full, drop
        finally:
            # Signal end to all consumers
            for queue in queues:
                try:
                    queue.put(None, timeout=0.1)
                except:
                    pass

    thread = Thread(target=reader_thread, daemon=True)
    thread.start()

    def make_consumer(queue):
        while not stop_event.is_set():
            try:
                item = queue.get(timeout=0.1)
                if item is None:
                    break
                yield item
            except Empty:
                continue

    return [make_consumer(q) for q in queues]


def filter_stream(
    stream: Iterator[Dict[str, Any]],
    predicate: Callable[[Dict[str, Any]], bool]
) -> Iterator[Dict[str, Any]]:
    """
    Filter stream items based on predicate.

    Args:
        stream: Input stream
        predicate: Function that returns True to keep item

    Yields:
        Dict: Filtered stream items

    Example:
        >>> # Only keep items where left button is clicked
        >>> filtered = filter_stream(
        ...     trackpad_stream(),
        ...     lambda item: item['left_click']
        ... )
    """
    for item in stream:
        if predicate(item):
            yield item


def map_stream(
    stream: Iterator[Dict[str, Any]],
    func: Callable[[Dict[str, Any]], Dict[str, Any]]
) -> Iterator[Dict[str, Any]]:
    """
    Transform stream items using function.

    Args:
        stream: Input stream
        func: Transformation function

    Yields:
        Dict: Transformed stream items

    Example:
        >>> def double_coords(item):
        ...     item['x_norm'] *= 2
        ...     item['y_norm'] *= 2
        ...     return item
        >>> transformed = map_stream(trackpad_stream(), double_coords)
    """
    for item in stream:
        yield func(item)


def monitor_stream(
    stream: Iterator[Dict[str, Any]],
    window_size: int = 100
) -> Iterator[Dict[str, Any]]:
    """
    Add statistics to stream items.

    Args:
        stream: Input stream
        window_size: Window size for computing stats

    Yields:
        Dict: Stream items with added '_stats' field

    Example:
        >>> for item in monitor_stream(trackpad_stream()):
        ...     print(f"Rate: {item['_stats']['rate_hz']:.1f} Hz")
    """
    timestamps = []
    count = 0

    for item in stream:
        current_time = timestamp()
        timestamps.append(current_time)
        count += 1

        # Keep only recent timestamps
        if len(timestamps) > window_size:
            timestamps.pop(0)

        # Compute stats
        if len(timestamps) >= 2:
            time_span = timestamps[-1] - timestamps[0]
            rate_hz = (len(timestamps) - 1) / time_span if time_span > 0 else 0
        else:
            rate_hz = 0

        # Add stats to item
        item['_stats'] = {
            'count': count,
            'rate_hz': rate_hz,
            'window_size': len(timestamps)
        }

        yield item
