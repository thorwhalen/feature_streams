"""
NETWORK_STREAM

Stream data over network using TCP sockets. Enables distributed streaming
applications where producers and consumers run on different machines.
"""

from .core import (
    stream_server,
    stream_client,
    NetworkConfig,
)

__version__ = "0.1.0"
__all__ = ["stream_server", "stream_client", "NetworkConfig"]
