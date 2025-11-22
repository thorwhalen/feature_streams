#!/usr/bin/env python3
"""
CLI for audio_input_stream package.

Usage:
    python -m audio_input_stream --preview
    python -m audio_input_stream --list-devices
    python -m audio_input_stream --record output.jsonl --duration 10
"""

import argparse
import sys
from . import audio_input_stream, AudioInputConfig, list_audio_devices
from ..util import record_stream


def main():
    parser = argparse.ArgumentParser(description='Audio input stream utility')
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--preview', action='store_true',
                      help='Preview audio features in terminal')
    group.add_argument('--list-devices', action='store_true',
                      help='List available audio input devices')
    group.add_argument('--record', metavar='FILE',
                      help='Record stream to file')

    parser.add_argument('--duration', type=int, default=10,
                       help='Duration in seconds (for record)')
    parser.add_argument('--device', type=int,
                       help='Audio device ID')

    args = parser.parse_args()

    if args.list_devices:
        devices = list_audio_devices()
        print("Available audio input devices:")
        print("=" * 50)
        for device in devices:
            print(f"  [{device['id']}] {device['name']}")
            print(f"      Channels: {device['channels']}, SR: {device['sample_rate']}")
        return

    config = AudioInputConfig(device=args.device)
    stream = audio_input_stream(config)

    if args.preview:
        print("Audio Feature Stream Preview (Press Ctrl+C to exit)")
        print("=" * 50)
        try:
            for item in stream:
                if item['is_voiced']:
                    print(f"Pitch: {item['pitch_hz']:6.1f} Hz, "
                          f"Conf: {item['pitch_confidence']:.2f}, "
                          f"Loud: {item['loudness_db']:5.1f} dB")
        except KeyboardInterrupt:
            print("\nExiting...")

    elif args.record:
        # Estimate items (audio updates faster than trackpad)
        max_items = int(args.duration * 20)  # ~20 Hz for audio features
        print(f"Recording to {args.record} for {args.duration}s...")
        try:
            record_stream(stream, args.record, max_items=max_items)
            print(f"Recording complete: {args.record}")
        except KeyboardInterrupt:
            print(f"\nRecording stopped: {args.record}")


if __name__ == "__main__":
    main()
