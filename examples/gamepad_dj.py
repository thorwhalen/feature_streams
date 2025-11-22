#!/usr/bin/env python3
"""
Gamepad DJ - Use gamepad as DJ controller for MIDI.

Dependencies:
    pip install pygame mido python-rtmidi

Usage:
    python examples/gamepad_dj.py

Controls:
    - Left stick X: Pitch bend
    - Right stick Y: Filter cutoff (CC 74)
    - Left trigger: Volume (CC 7)
    - Right trigger: Reverb (CC 91)
    - Buttons: Trigger different notes
    - Ctrl+C: Exit
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gamepad_stream import gamepad_stream, list_gamepads
from midi_out_stream import midi_out_stream_consumer, MIDIConfig
from transforms import linear_map


def gamepad_to_midi_dj():
    """
    Map gamepad controls to MIDI for DJ-style control.
    """
    # Check for gamepad
    gamepads = list_gamepads()
    if not gamepads:
        print("❌ No gamepad detected! Please connect a gamepad.")
        return

    print("🎮 Gamepad DJ Controller")
    print(f"   Using: {gamepads[0]}")
    print("   Left stick X: Pitch bend")
    print("   Right stick Y: Filter cutoff")
    print("   Left trigger: Volume")
    print("   Right trigger: Reverb")
    print("   Buttons: Trigger notes")
    print("   Press Ctrl+C to exit\n")

    last_buttons = {}
    note_assignments = {
        'button_0': 60,  # C
        'button_1': 62,  # D
        'button_2': 64,  # E
        'button_3': 65,  # F
        'button_4': 67,  # G
        'button_5': 69,  # A
    }

    for state in gamepad_stream():
        # Pitch bend from left stick X
        pitch_bend_value = int(state['left_stick_x'] * 8191)
        yield {
            'event_type': 'pitch_bend',
            'pitch_bend': pitch_bend_value,
            'channel': 0
        }

        # Filter cutoff from right stick Y
        filter_cc = int(linear_map(
            state['right_stick_y'],
            (-1, 1),
            (0, 127)
        ))
        yield {
            'event_type': 'cc',
            'cc_number': 74,  # Filter cutoff
            'cc_value': filter_cc,
            'channel': 0
        }

        # Volume from left trigger
        volume_cc = int(state['left_trigger'] * 127)
        yield {
            'event_type': 'cc',
            'cc_number': 7,  # Volume
            'cc_value': volume_cc,
            'channel': 0
        }

        # Reverb from right trigger
        reverb_cc = int(state['right_trigger'] * 127)
        yield {
            'event_type': 'cc',
            'cc_number': 91,  # Reverb
            'cc_value': reverb_cc,
            'channel': 0
        }

        # Button triggers for notes
        for button, note in note_assignments.items():
            current_state = state['button_states'].get(button, False)
            last_state = last_buttons.get(button, False)

            if current_state and not last_state:
                # Button pressed
                yield {
                    'event_type': 'note',
                    'midi_note': note,
                    'velocity': 100,
                    'channel': 0
                }
            elif not current_state and last_state:
                # Button released
                yield {
                    'event_type': 'note',
                    'midi_note': note,
                    'velocity': 0,
                    'channel': 0
                }

            last_buttons[button] = current_state


if __name__ == "__main__":
    try:
        config = MIDIConfig(create_virtual_port=True, virtual_port_name="Gamepad DJ")
        print("Created virtual MIDI port: 'Gamepad DJ'\n")

        midi_out_stream_consumer(gamepad_to_midi_dj(), config)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
