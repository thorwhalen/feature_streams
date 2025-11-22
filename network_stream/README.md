# NETWORK_STREAM

Stream data over network using TCP sockets. Enables distributed streaming applications where producers and consumers run on different machines.

## Features

- TCP-based streaming (reliable, ordered delivery)
- JSON serialization
- Length-prefixed messages
- Automatic reconnection support (server-side)
- Simple client-server architecture

## Installation

No additional dependencies required (uses Python built-in `socket` module).

## Usage

### Server (Stream Producer)

```python
from trackpad_stream import trackpad_stream
from network_stream import stream_server, NetworkConfig

config = NetworkConfig(host='0.0.0.0', port=5000)
stream_server(trackpad_stream(), config)
```

### Client (Stream Consumer)

```python
from network_stream import stream_client
from synth_stream import synth_stream_consumer

# Receive stream from network
network_stream = stream_client('192.168.1.100', 5000)

# Use it like any other stream
synth_stream_consumer(network_stream)
```

## Configuration

```python
NetworkConfig(
    host='0.0.0.0',  # Server: 0.0.0.0 for all interfaces, Client: server IP
    port=5000,        # Port number
    buffer_size=4096  # Socket buffer size
)
```

## Examples

### Example 1: Remote Theremin

**Machine A (with trackpad):**
```python
from trackpad_stream import trackpad_stream
from network_stream import stream_server

print("Streaming trackpad data...")
stream_server(trackpad_stream(), port=5000)
```

**Machine B (with audio output):**
```python
from network_stream import stream_client
from synth_stream import synth_stream_consumer
from transforms import linear_map

def network_to_synth():
    for item in stream_client('machine-a.local', 5000):
        yield {
            'pitch_hz': linear_map(item['x_norm'], (0, 1), (200, 800)),
            'amplitude': item['y_norm'],
            'waveform_type': 'sine'
        }

synth_stream_consumer(network_to_synth())
```

### Example 2: Distributed Processing

**Producer:**
```python
from audio_input_stream import audio_input_stream
from network_stream import stream_server

stream_server(audio_input_stream(), port=5001)
```

**Consumer:**
```python
from network_stream import stream_client
from viz_stream import viz_stream_consumer, VizConfig

config = VizConfig(fields=['pitch_hz', 'loudness_db'])
viz_stream_consumer(stream_client('localhost', 5001), config)
```

## Network Considerations

### Latency
- TCP introduces ~10-50ms latency on LAN
- WAN latency depends on distance and connection quality
- For lowest latency, use LAN or localhost

### Bandwidth
- JSON encoding is human-readable but not most efficient
- Typical stream item: ~200-500 bytes
- At 60Hz: ~12-30 KB/s bandwidth required

### Firewall
Make sure firewall allows connections on chosen port:
```bash
# Linux
sudo ufw allow 5000/tcp

# macOS
# System Preferences > Security & Privacy > Firewall > Firewall Options
```

## Error Handling

The server automatically handles client disconnections and waits for new connections. The client will raise an exception on disconnect.

## Testing

Test locally using localhost:

**Terminal 1 (Server):**
```python
python -c "from trackpad_stream import trackpad_stream; from network_stream import stream_server; stream_server(trackpad_stream())"
```

**Terminal 2 (Client):**
```python
python -c "from network_stream import stream_client; [print(item) for item in stream_client()]"
```

## Notes

- Uses JSON for serialization (simple but not most efficient)
- TCP ensures reliable, ordered delivery
- Server can handle one client at a time (sequential connections)
- No authentication or encryption (use SSH tunneling for security)
- For UDP (lower latency, unreliable), consider extending this package

## Security Warning

This implementation has no authentication or encryption. Only use on trusted networks or tunnel through SSH:

```bash
# SSH tunnel example
ssh -L 5000:localhost:5000 user@remote-machine
```

## Dependencies

None (uses Python standard library only)
