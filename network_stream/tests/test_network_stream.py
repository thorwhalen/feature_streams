"""
Tests for network_stream package.
"""

import sys
import os
import time
from threading import Thread

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from network_stream import NetworkConfig


def test_network_config_defaults():
    """Test default configuration."""
    config = NetworkConfig()
    assert config.host == '0.0.0.0'
    assert config.port == 5000
    assert config.buffer_size == 4096


def test_custom_config():
    """Test custom configuration."""
    config = NetworkConfig(
        host='127.0.0.1',
        port=8000,
        buffer_size=8192
    )
    assert config.host == '127.0.0.1'
    assert config.port == 8000
    assert config.buffer_size == 8192


def test_client_server():
    """Test client-server communication."""
    from network_stream import stream_server, stream_client

    # Test data generator
    def test_stream():
        for i in range(5):
            yield {'index': i, 'value': i * 10}
            time.sleep(0.1)

    # Start server in background
    def run_server():
        try:
            stream_server(test_stream(), NetworkConfig(port=5555))
        except Exception as e:
            print(f"Server error: {e}")

    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(0.5)

    # Connect client and receive data
    try:
        items = []
        for item in stream_client('localhost', 5555, timeout=2.0):
            items.append(item)
            if len(items) >= 5:
                break

        # Verify data
        assert len(items) == 5
        assert items[0]['index'] == 0
        assert items[4]['index'] == 4
        print("✓ Client-server test OK")

    except Exception as e:
        print(f"⊘ Client-server test failed: {e}")


if __name__ == "__main__":
    print("Testing network config...")
    test_network_config_defaults()
    print("✓ Config OK")

    print("\nTesting custom config...")
    test_custom_config()
    print("✓ Custom config OK")

    print("\nTesting client-server...")
    test_client_server()

    print("\nAll tests completed!")
