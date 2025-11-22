"""
Core implementation for text-to-speech stream consumer.
"""

import sys
import os
from typing import Iterator, Dict, Any, Optional, List
from dataclasses import dataclass
from queue import Queue, Empty
from threading import Thread, Event
import warnings

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp

# Import TTS dependencies
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    warnings.warn("pyttsx3 not installed. Install with: pip install pyttsx3")


@dataclass
class TTSConfig:
    """Configuration for TTS engine."""
    default_rate: int = 150  # Words per minute
    default_volume: float = 0.8  # 0.0 to 1.0
    default_voice: Optional[str] = None  # None = system default
    queue_max_size: int = 10  # Max items in speech queue


def list_voices() -> List[Dict[str, str]]:
    """
    List available TTS voices.

    Returns:
        List of dicts with voice info: {'id': ..., 'name': ..., 'languages': [...]}
    """
    if not PYTTSX3_AVAILABLE:
        return []

    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    result = []
    for voice in voices:
        result.append({
            'id': voice.id,
            'name': voice.name,
            'languages': getattr(voice, 'languages', [])
        })

    engine.stop()
    del engine

    return result


class TTSEngine:
    """Text-to-speech engine wrapper."""

    def __init__(self, config: TTSConfig):
        if not PYTTSX3_AVAILABLE:
            raise RuntimeError("pyttsx3 not installed")

        self.config = config
        self.engine = pyttsx3.init()

        # Set defaults
        self.engine.setProperty('rate', config.default_rate)
        self.engine.setProperty('volume', config.default_volume)

        if config.default_voice:
            self.engine.setProperty('voice', config.default_voice)

        # Speech queue
        self.speech_queue = Queue(maxsize=config.queue_max_size)
        self.stop_event = Event()

        # Track state
        self.is_speaking = False

        # Start speech worker thread
        self.worker_thread = Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def _speech_worker(self):
        """Worker thread that processes speech queue."""
        while not self.stop_event.is_set():
            try:
                # Get next speech item
                item = self.speech_queue.get(timeout=0.1)

                # Update parameters
                if 'rate' in item:
                    rate = max(50, min(300, item['rate']))
                    self.engine.setProperty('rate', rate)

                if 'volume' in item:
                    volume = max(0.0, min(1.0, item['volume']))
                    self.engine.setProperty('volume', volume)

                if 'voice_id' in item and item['voice_id']:
                    self.engine.setProperty('voice', item['voice_id'])

                # Check priority (high priority clears queue)
                if item.get('priority', 0) > 0:
                    # Clear any pending speech
                    self.engine.stop()
                    # Drain queue
                    while not self.speech_queue.empty():
                        try:
                            self.speech_queue.get_nowait()
                        except Empty:
                            break

                # Speak text
                text = item.get('text', '')
                if text:
                    self.is_speaking = True
                    self.engine.say(text)
                    self.engine.runAndWait()
                    self.is_speaking = False

            except Empty:
                continue
            except Exception as e:
                warnings.warn(f"TTS worker error: {e}")

    def speak(self, text_dict: Dict[str, Any]):
        """
        Queue text for speaking.

        Args:
            text_dict: Text control dictionary
        """
        try:
            self.speech_queue.put(text_dict, timeout=0.1)
        except:
            # Queue full, drop item
            pass

    def is_idle(self) -> bool:
        """Check if engine is idle (not speaking)."""
        return not self.is_speaking and self.speech_queue.empty()

    def stop(self):
        """Stop engine and worker thread."""
        self.stop_event.set()
        self.engine.stop()
        self.worker_thread.join(timeout=1.0)


def tts_stream_consumer(
    text_stream: Iterator[Dict[str, Any]],
    config: Optional[TTSConfig] = None
):
    """
    Consume text stream and generate speech output.

    Args:
        text_stream: Iterator yielding text control dictionaries
        config: Optional TTS configuration

    Example:
        >>> def text_gen():
        ...     texts = ["Hello world", "How are you?", "Goodbye"]
        ...     for text in texts:
        ...         yield {'text': text, 'rate': 150, 'volume': 0.8}
        ...         time.sleep(1.0)
        >>>
        >>> tts_stream_consumer(text_gen())
    """
    if config is None:
        config = TTSConfig()

    engine = TTSEngine(config)

    try:
        for text_dict in text_stream:
            engine.speak(text_dict)
    finally:
        # Wait a bit for final speech to complete
        import time
        timeout = 5.0
        start = time.time()
        while not engine.is_idle() and (time.time() - start) < timeout:
            time.sleep(0.1)

        engine.stop()
