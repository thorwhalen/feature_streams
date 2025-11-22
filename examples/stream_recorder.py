#!/usr/bin/env python3
"""
Stream Recorder - Record and playback streams for testing.

Dependencies:
    pip install pynput

Usage:
    # Record
    python examples/stream_recorder.py record trackpad recording.jsonl --duration 10

    # Playback
    python examples/stream_recorder.py playback recording.jsonl

    # Playback at 2x speed
    python examples/stream_recorder.py playback recording.jsonl --speed 2.0
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util import record_stream, playback_stream


def main():
    parser = argparse.ArgumentParser(description='Record and playback streams')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Record command
    record_parser = subparsers.add_parser('record', help='Record a stream')
    record_parser.add_argument('source', choices=['trackpad', 'keyboard', 'gamepad', 'audio'],
                              help='Input stream source')
    record_parser.add_argument('output', help='Output file (.jsonl)')
    record_parser.add_argument('--duration', type=int, default=10,
                              help='Recording duration in seconds')
    record_parser.add_argument('--max-items', type=int, help='Max items to record')

    # Playback command
    playback_parser = subparsers.add_parser('playback', help='Playback a recorded stream')
    playback_parser.add_argument('input', help='Input file (.jsonl)')
    playback_parser.add_argument('--speed', type=float, default=1.0,
                                help='Playback speed multiplier')
    playback_parser.add_argument('--no-realtime', action='store_true',
                                help='Playback as fast as possible')

    args = parser.parse_args()

    if args.command == 'record':
        # Import appropriate stream
        if args.source == 'trackpad':
            from trackpad_stream import trackpad_stream
            stream = trackpad_stream()
        elif args.source == 'keyboard':
            from keyboard_stream import keyboard_stream
            stream = keyboard_stream()
        elif args.source == 'gamepad':
            from gamepad_stream import gamepad_stream
            stream = gamepad_stream()
        elif args.source == 'audio':
            from audio_input_stream import audio_input_stream
            stream = audio_input_stream()

        # Calculate max items from duration
        if args.max_items is None:
            # Assume 60 Hz stream
            args.max_items = args.duration * 60

        print(f"📹 Recording {args.source} stream to {args.output}")
        print(f"   Duration: {args.duration}s (~{args.max_items} items)")
        print("   Press Ctrl+C to stop early\n")

        try:
            record_stream(stream, args.output, max_items=args.max_items)
            print(f"\n✅ Recording complete: {args.output}")
        except KeyboardInterrupt:
            print(f"\n⏸️  Recording stopped: {args.output}")

    elif args.command == 'playback':
        print(f"▶️  Playing back {args.input}")
        print(f"   Speed: {args.speed}x")
        print(f"   Realtime: {not args.no_realtime}\n")

        try:
            count = 0
            for item in playback_stream(args.input,
                                       realtime=not args.no_realtime,
                                       speed=args.speed):
                count += 1
                if count % 60 == 0:
                    print(f"   Items: {count}", end='\r')

            print(f"\n✅ Playback complete: {count} items")
        except KeyboardInterrupt:
            print(f"\n⏸️  Playback stopped at item {count}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
