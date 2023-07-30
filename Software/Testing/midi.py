from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange

from setup import (
    midi_serial,
    midi_usb,
)


# MIDI Functions
def send_note_on(note, octv):
    note = (note) + (12 * octv)
    midi_serial.send(NoteOn(note, 120))
    midi_usb.send(NoteOn(note, 120))


def send_note_off(note, octv):
    note = (note) + (12 * octv)
    midi_serial.send(NoteOff(note, 0))
    midi_usb.send(NoteOff(note, 120))


def send_cc(number, val):
    midi_serial.send(ControlChange(number, val))
    midi_usb.send(ControlChange(number, val))
