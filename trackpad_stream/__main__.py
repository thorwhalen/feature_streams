#!/usr/bin/env python3
"""
CLI for trackpad_stream package.

Usage:
    python -m trackpad_stream --preview
    python -m trackpad_stream --record output.jsonl --duration 10
"""

import argparse
import sys
from . import trackpad_stream, TrackpadConfig
from ..util import record_stream


def main():
    parser = argparse.ArgumentParser(description='Trackpad stream utility')
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--preview', action='store_true',
                      help='Preview trackpad stream in terminal')
    group.add_argument('--record', metavar='FILE',
                      help='Record stream to file')

    parser.add_argument('--duration', type=int, default=10,
                       help='Duration in seconds (for record)')
    parser.add_argument('--rate', type=float, default=60.0,
                       help='Sample rate in Hz')

    args = parser.parse_args()

    config = TrackpadConfig(rate_hz=args.rate)
    stream = trackpad_stream(config)

    if args.preview:
        print("Trackpad Stream Preview (Press Ctrl+C to exit)")
        print("=" * 50)
        try:
            for i, item in enumerate(stream):
                if i % 10 == 0:  # Print every 10th item
                    print(f"X: {item['x_norm']:.2f}, Y: {item['y_norm']:.2f}, "
                          f"L: {item['left_click']}, R: {item['right_click']}")
        except KeyboardInterrupt:
            print("\nExiting...")

    elif args.record:
        max_items = int(args.duration * args.rate)
        print(f"Recording to {args.record} for {args.duration}s...")
        try:
            record_stream(stream, args.record, max_items=max_items)
            print(f"Recording complete: {args.record}")
        except KeyboardInterrupt:
            print(f"\nRecording stopped: {args.record}")


if __name__ == "__main__":
    main()
