import terminalio
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_display_text import label
from State import State

from setup import (
    display,
    keys,
    midi_serial,
    midi_usb,
    neopixels,
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


class MIDIState(State):
    @property
    def name(self):
        return "midi_controller"

    def enter(self, machine):
        text = "MIDI Controller"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
        display.show(text_area)
        neopixels.fill((100, 100, 100))
        neopixels.show()
        self.notes = []
        State.enter(self, machine)

    def exit(self, machine):
        for key in self.notes:
            send_note_off(key, 4)
        self.notes = []
        neopixels.fill((100, 100, 100))
        neopixels.show()
        State.exit(self, machine)

    def update(self, machine):
        key_event = keys.events.get()
        while key_event:
            if key_event.key_number < 10:
                if key_event.pressed:
                    key = key_event.key_number
                    self.notes.append(key)
                    send_note_on(key, 4)
                    neopixels[key] = (255, 0, 0)
                if key_event.released:
                    key = key_event.key_number
                    if key in self.notes:
                        self.notes.remove(key)
                    send_note_off(key, 4)
                    neopixels[key] = (100, 100, 100)
            elif (key_event.key_number == 10) and key_event.pressed:  # Select Button
                machine.go_to_state("menu")
                return
            elif (key_event.key_number == 11) and key_event.pressed:  # Volume Button
                print("TODO: Decide what the volume button does")
            key_event = keys.events.get()

        neopixels.show()
