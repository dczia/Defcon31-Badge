"""End-to-end regression for the USB HID crash.

This drives HIDState the way the firmware does - post a key event, call
update() - and asserts it survives. Against the original neoindex mapping,
pressing Play or Function here raises IndexError from neopixels[10].
"""

import circuitpython_stubs
import setup
from HIDState import HIDState


class FakeMachine:
    """Stand-in for StateMachine; records transitions instead of making them."""

    def __init__(self):
        self.animation = None
        self.last_state = None
        self.transitions = []

    def go_to_state(self, name):
        self.transitions.append(name)


def press(key_number):
    setup.keys.events.post(circuitpython_stubs.Event(key_number, pressed=True))


def release(key_number):
    setup.keys.events.post(circuitpython_stubs.Event(key_number, pressed=False))


def make_state():
    machine = FakeMachine()
    state = HIDState()
    setup.keys.events.clear()
    state.enter(machine)
    return state, machine


def test_pressing_play_does_not_crash():
    """Key 8 is Play. This is the exact crash that dropped the badge to REPL."""
    state, machine = make_state()
    press(8)
    state.update(machine)


def test_pressing_function_does_not_crash():
    """Key 9 is Function."""
    state, machine = make_state()
    press(9)
    state.update(machine)


def test_every_pad_press_and_release_is_survivable():
    state, machine = make_state()
    for key_number in range(10):
        press(key_number)
        release(key_number)
    state.update(machine)


def test_pad_press_sends_a_keycode():
    state, machine = make_state()
    press(0)
    state.update(machine)
    assert state.kbd.pressed, "pressing a pad should press a key"


def test_select_button_returns_to_menu():
    """Key 10 is the select encoder button."""
    state, machine = make_state()
    press(10)
    state.update(machine)
    assert machine.transitions == ["menu"]
