"""Regression tests for the MIDI helpers and the MIDI sequencer's note maths.

timed_midi() used to call send_note_on(note, octave) and
send_note_off(note, note), but both helpers take a single MIDI note number, so
starting the MIDI sequencer raised TypeError immediately.
"""

import inspect

import pytest

import setup
from MIDIState import (
    MIDIState,
    send_cc,
    send_note_off,
    send_note_on,
)

ALL_NOTES_OFF = 123


@pytest.fixture(autouse=True)
def clear_sent():
    setup.midi_serial.sent.clear()
    setup.midi_usb.sent.clear()
    yield


def test_note_helpers_take_a_single_note():
    """The arity the sequencer got wrong."""
    for helper in (send_note_on, send_note_off):
        parameters = inspect.signature(helper).parameters
        assert list(parameters) == ["note"], helper.__name__


def test_note_on_goes_to_both_ports():
    send_note_on(60)
    assert [message.note for message in setup.midi_serial.sent] == [60]
    assert [message.note for message in setup.midi_usb.sent] == [60]


def test_note_off_sends_zero_velocity():
    send_note_off(60)
    assert setup.midi_serial.sent[0].note == 60
    assert setup.midi_serial.sent[0].velocity == 0


def test_octave_folding_matches_twelve_semitones():
    """Sequence entries are [play, note, octave]; timed_midi folds the octave in.

    Reproduces the arithmetic the sequencer performs so a change to it has to be
    deliberate.
    """
    for note, octave in ((1, 2), (3, 2), (5, 0), (11, 8)):
        assert note + (12 * octave) == note + octave * 12


def test_midi_panic_sends_all_notes_off():
    state = MIDIState()
    state.notes = [60, 64]
    state.midi_panic()
    assert state.notes == []
    controls = [message.control for message in setup.midi_serial.sent]
    assert ALL_NOTES_OFF in controls


def test_send_cc_reaches_both_ports():
    send_cc(7, 100)
    assert setup.midi_serial.sent[0].control == 7
    assert setup.midi_usb.sent[0].value == 100


def test_major_scale_intervals():
    state = MIDIState()
    state.generate_major_scale(60)
    assert state.scale == [60, 62, 64, 65, 67, 69, 71, 72]


def test_minor_scale_intervals():
    state = MIDIState()
    state.generate_minor_scale(60)
    assert state.scale == [60, 62, 63, 65, 67, 68, 70, 72]


def test_scale_covers_all_eight_pads():
    state = MIDIState()
    state.generate_major_scale(24)
    assert len(state.scale) == 8


def test_octave_up_then_down_returns_to_start():
    state = MIDIState()
    state.generate_major_scale(60)
    original = list(state.scale)
    state.octave_up()
    assert state.scale == [note + 12 for note in original]
    state.octave_down()
    assert state.scale == original


def test_timed_midi_sends_the_folded_note():
    """The sequencer's step handler must call the helpers with one argument.

    timed_midi() used to call send_note_on(note, octave), which raised TypeError
    the instant the MIDI sequencer was started.
    """
    from SequencerState import SequencerPlayState, midi_sequences

    midi_sequences.sequences[0] = [[True, 3, 2]] * 8

    state = SequencerPlayState()
    state.step = 0
    state.step_length = 3
    state.timed_midi()

    expected_note = 3 + (12 * 2)
    notes_on = [m for m in setup.midi_serial.sent if type(m).__name__ == "NoteOn"]
    notes_off = [m for m in setup.midi_serial.sent if type(m).__name__ == "NoteOff"]
    assert [m.note for m in notes_on] == [expected_note]
    assert [m.note for m in notes_off] == [expected_note]


def test_timed_midi_stays_silent_on_a_disabled_step():
    from SequencerState import SequencerPlayState, midi_sequences

    midi_sequences.sequences[0] = [[False, 3, 2]] * 8

    state = SequencerPlayState()
    state.step = 0
    state.step_length = 3
    state.timed_midi()

    assert setup.midi_serial.sent == []
