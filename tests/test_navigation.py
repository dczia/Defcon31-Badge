"""Tests for menu navigation, the startup sequence and LED animation modes.

These states are pure UI: they read encoder positions and key events, redraw the
display, and hand control to the state machine. They had no coverage at all, so
a change to scrolling or to a menu's wiring could not be caught before flashing
a badge.
"""

import pytest

import circuitpython_stubs
import setup
from FlashyState import FlashyState
from MenuState import MenuState
from StartupState import StartupState
from utils import selector_calcs, show_menu

TOTAL_LINES = 3


class FakeMachine:
    def __init__(self):
        self.animation = None
        self.last_state = None
        self.transitions = []

    def go_to_state(self, name):
        self.transitions.append(name)


@pytest.fixture(autouse=True)
def clean_input():
    setup.keys.events.clear()
    setup.select_enc.position = 0
    setup.volume_enc.position = 0
    yield
    setup.keys.events.clear()


def press(key_number):
    setup.keys.events.post(circuitpython_stubs.Event(key_number, pressed=True))


# --- selector_calcs -------------------------------------------------------


def test_selector_scrolls_down_within_the_visible_window():
    highlight, shift = selector_calcs(["a"] * 6, 1, 0, 0, 1)
    assert (highlight, shift) == (2, 0)


def test_selector_shifts_the_window_once_it_reaches_the_bottom():
    highlight, shift = selector_calcs(["a"] * 6, TOTAL_LINES, 0, 0, 1)
    assert (highlight, shift) == (TOTAL_LINES, 1)


def test_selector_stops_at_the_end_of_the_list():
    length = 4
    highlight, shift = selector_calcs(["a"] * length, TOTAL_LINES, 1, 0, 1)
    assert (highlight, shift) == (TOTAL_LINES, 1)


def test_selector_scrolls_up_and_stops_at_the_top():
    highlight, shift = selector_calcs(["a"] * 6, 1, 0, 1, 0)
    assert (highlight, shift) == (1, 0)


def test_selector_unshifts_before_moving_the_highlight_up():
    highlight, shift = selector_calcs(["a"] * 6, 1, 2, 1, 0)
    assert (highlight, shift) == (1, 1)


# --- show_menu ------------------------------------------------------------


def test_show_menu_renders_the_visible_window():
    menu = [{"pretty": "one"}, {"pretty": "two"}, {"pretty": "three"}]
    show_menu(menu, 1, 0)
    assert setup.display.shown is not None


def test_show_menu_tolerates_a_list_shorter_than_the_window():
    show_menu([{"pretty": "only"}], 1, 0)
    assert setup.display.shown is not None


def test_show_menu_handles_an_empty_menu():
    show_menu([], 1, 0)
    assert setup.display.shown is not None


# --- MenuState ------------------------------------------------------------


def test_menu_starts_an_animation_on_entry():
    machine = FakeMachine()
    MenuState().enter(machine)
    assert machine.animation is not None


def test_menu_reuses_an_existing_animation():
    machine = FakeMachine()
    machine.animation = "already running"
    MenuState().enter(machine)
    assert machine.animation == "already running"


def test_turning_the_encoder_moves_the_highlight():
    machine = FakeMachine()
    state = MenuState()
    state.enter(machine)
    before = state.highlight
    setup.select_enc.position = 1
    state.update(machine)
    assert state.highlight == before + 1


def test_selecting_the_first_entry_enters_flashy():
    machine = FakeMachine()
    state = MenuState()
    state.enter(machine)
    press(0)
    state.update(machine)
    assert machine.transitions == ["flashy"]


def test_every_menu_entry_names_a_registered_state():
    """Guards against a menu entry pointing at a state that does not exist."""
    known = {
        "flashy",
        "sampler_menu",
        "sequencer_menu",
        "midi_controller",
        "hid",
        "startup",
    }
    for item in MenuState.menu_items:
        assert item["name"] in known, item


def test_scrolling_past_the_window_shifts_the_list():
    machine = FakeMachine()
    state = MenuState()
    state.enter(machine)
    for step in range(1, 6):
        setup.select_enc.position = step
        state.update(machine)
    assert state.shift > 0
    index = state.highlight - 1 + state.shift
    assert index < len(MenuState.menu_items)


# --- FlashyState ----------------------------------------------------------


def test_flashy_selects_an_animation_when_scrolled():
    machine = FakeMachine()
    state = FlashyState()
    state.enter(machine)
    setup.select_enc.position = 1
    state.update(machine)
    assert machine.animation is not None


@pytest.mark.parametrize(
    "name",
    ["rainbow", "rainbow_chase", "rainbow_comet", "rainbow_sparkle", "sparkle_pulse"],
)
def test_every_flashy_animation_can_be_constructed(name):
    machine = FakeMachine()
    FlashyState().animation_selector(machine, name)
    assert machine.animation is not None


def test_flashy_menu_functions_are_all_selectable():
    machine = FakeMachine()
    state = FlashyState()
    for item in FlashyState.menu_items:
        state.animation_selector(machine, item["function"])
        assert machine.animation is not None, item


def test_flashy_returns_to_the_menu_on_keypress():
    machine = FakeMachine()
    state = FlashyState()
    state.enter(machine)
    press(0)
    state.update(machine)
    assert machine.transitions == ["menu"]


def test_animations_take_ownership_of_auto_write():
    """adafruit_led_animation sets auto_write False; firmware relies on it."""
    machine = FakeMachine()
    setup.neopixels.auto_write = True
    FlashyState().animation_selector(machine, "rainbow")
    assert setup.neopixels.auto_write is False


# --- StartupState ---------------------------------------------------------


def test_startup_advances_through_its_stages():
    machine = FakeMachine()
    state = StartupState()
    state.enter(machine)
    for _ in range(3000):
        state.update(machine)
        if machine.transitions:
            break
    assert machine.transitions == ["menu"]


def test_startup_is_skipped_by_a_keypress():
    machine = FakeMachine()
    state = StartupState()
    state.enter(machine)
    press(0)
    state.update(machine)
    assert machine.transitions == ["menu"]


def test_startup_never_addresses_a_pixel_it_does_not_have():
    """Stage two walks the strip by index; it must stay inside it."""
    machine = FakeMachine()
    state = StartupState()
    state.enter(machine)
    for _ in range(3000):
        state.update(machine)
        if machine.transitions:
            break


def test_startup_clears_the_strip_on_entry():
    machine = FakeMachine()
    setup.neopixels.fill((9, 9, 9))
    StartupState().enter(machine)
    assert setup.neopixels[0] == (0, 0, 0)
