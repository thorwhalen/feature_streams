"""
Core implementation for network streaming.
"""

import sys
import os
import socket
import json
from typing import Iterator, Dict, Any, Optional
from dataclasses import dataclass
import struct

# Import parent util module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import timestamp


@dataclass
class NetworkConfig:
    """Configuration for network streaming."""
    host: str = '0.0.0.0'
    port: int = 5000
    buffer_size: int = 4096


def stream_server(
    stream: Iterator[Dict[str, Any]],
    config: Optional[NetworkConfig] = None
):
    """
    Stream server - send stream data over network.

    Args:
        stream: Input stream to send
        config: Optional network configuration

    Example:
        >>> from trackpad_stream import trackpad_stream
        >>> stream_server(trackpad_stream(), NetworkConfig(port=5000))
    """
    if config is None:
        config = NetworkConfig()

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((config.host, config.port))
    server_socket.listen(1)

    print(f"Stream server listening on {config.host}:{config.port}")

    try:
        while True:
            # Accept connection
            client_socket, client_address = server_socket.accept()
            print(f"Client connected from {client_address}")

            try:
                # Send stream items
                for item in stream:
                    # Serialize to JSON
                    data = json.dumps(item).encode('utf-8')

                    # Send length prefix (4 bytes) + data
                    length = struct.pack('!I', len(data))
                    client_socket.sendall(length + data)

            except (BrokenPipeError, ConnectionResetError):
                print(f"Client {client_address} disconnected")
            finally:
                client_socket.close()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()


def stream_client(
    host: str = 'localhost',
    port: int = 5000,
    timeout: Optional[float] = None
) -> Iterator[Dict[str, Any]]:
    """
    Stream client - receive stream data from network.

    Args:
        host: Server hostname or IP
        port: Server port
        timeout: Socket timeout in seconds (None = no timeout)

    Yields:
        Dict: Stream items from server

    Example:
        >>> for item in stream_client('localhost', 5000):
        ...     print(item)
    """
    # Connect to server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if timeout:
        client_socket.settimeout(timeout)

    client_socket.connect((host, port))
    print(f"Connected to server {host}:{port}")

    try:
        while True:
            # Receive length prefix (4 bytes)
            length_data = _recv_exactly(client_socket, 4)
            if not length_data:
                break

            length = struct.unpack('!I', length_data)[0]

            # Receive data
            data = _recv_exactly(client_socket, length)
            if not data:
                break

            # Deserialize
            item = json.loads(data.decode('utf-8'))
            yield item

    except (ConnectionResetError, socket.timeout):
        print("Connection lost")
    finally:
        client_socket.close()


def _recv_exactly(sock: socket.socket, n: int) -> bytes:
    """
    Receive exactly n bytes from socket.

    Args:
        sock: Socket to receive from
        n: Number of bytes to receive

    Returns:
        bytes: Received data (or empty if connection closed)
    """
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return b''  # Connection closed
        data += chunk
    return data
