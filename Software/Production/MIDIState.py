import terminalio
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_display_text import label
from State import State

from utils import (
    neoindex,
)
from setup import (
    display,
    keys,
    midi_serial,
    midi_usb,
    neopixels,
    select_enc,
    volume_enc,
)

c_1 = 24
d_1 = 26
e_1 = 28
f_1 = 29
g_1 = 31
a_1 = 33
b_1 = 35

# MIDI Functions
# def send_note_on(note, octv):
#     note = (note) + (12 * octv)
#     midi_serial.send(NoteOn(note, 120))
#     midi_usb.send(NoteOn(note, 120))


# def send_note_off(note, octv):
#     note = (note) + (12 * octv)
#     midi_serial.send(NoteOff(note, 0))
#     midi_usb.send(NoteOff(note, 120))

# MIDI Functions
def send_note_on(note):
    midi_serial.send(NoteOn(note, 120))
    midi_usb.send(NoteOn(note, 120))


def send_note_off(note):
    midi_serial.send(NoteOff(note, 0))
    midi_usb.send(NoteOff(note, 0))


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
        # Reset encoder positions
        select_enc.position = 0
        volume_enc.position = 0
        self.last_select_position = select_enc.position
        self.last_volume_position = volume_enc.position
        self.notes = []  # Current pressed notes
        self.scale = []  # Current scale
        self.base = c_1  # Current base note
        self.current_scale = "major"
        self.generate_major_scale(self.base)
        keys.events.clear()
        State.enter(self, machine)

    def exit(self, machine):
        self.midi_panic()
        neopixels.fill((100, 100, 100))
        neopixels.show()
        State.exit(self, machine)

    def generate_major_scale(self, base):
        self.scale = []
        pattern = [0, 2, 4, 5, 7, 9, 11, 12]
        for value in pattern:
            self.scale.append(base + value)

    def generate_minor_scale(self, base):
        self.scale = []
        pattern = [0, 2, 3, 5, 7, 8, 10, 12]
        for value in pattern:
            self.scale.append(base + value)

    def midi_panic(self):
        send_cc(123, 0)  # Turn off all MIDI signal
        self.notes = []

    def base_down(self):
        if self.base > 24:
            self.base = self.base - 1

    def base_up(self):
        if self.base < 108:
            self.base = self.base + 1

    def octave_down(self):
        if self.scale[0] >= 36:
            for index, note in enumerate(self.scale):
                self.scale[index] = note - 12
            self.midi_panic()  # TODO improve tracking
            self.base = self.scale[0]

    def octave_up(self):
        if self.scale[0] <= 108:
            for index, note in enumerate(self.scale):
                self.scale[index] = note + 12
            self.midi_panic()  # TODO improve tracking
            self.base = self.scale[0]

    def poll_encoders(self):
        # Check select knob
        if select_enc.position != self.last_select_position:
            if select_enc.position < self.last_select_position:
                self.octave_down()
            if select_enc.position > self.last_select_position:
                self.octave_up()
            self.last_select_position = select_enc.position

        # Check volume knob
        if volume_enc.position != self.last_volume_position:
            # Change to minor if already major
            if self.current_scale == "major":
                self.generate_minor_scale(self.base)
                self.current_scale = "minor"
            # Change to major if already minor
            elif self.current_scale == "minor":
                self.generate_major_scale(self.base)
                self.current_scale = "major"
            self.last_volume_position = volume_enc.position

    def update(self, machine):
        key_event = keys.events.get()
        if key_event:
            if key_event.key_number < 8:
                if key_event.pressed:
                    key = key_event.key_number
                    note_value = self.scale[key]
                    self.notes.append(note_value)
                    send_note_on(note_value)
                    mapped_neopixel = neoindex(key)
                    neopixels[mapped_neopixel] = (255, 0, 0)
                if key_event.released:
                    key = key_event.key_number
                    note_value = self.scale[key]
                    if note_value in self.notes:
                        self.notes.remove(note_value)
                    send_note_off(note_value)
                    mapped_neopixel = neoindex(key)
                    neopixels[mapped_neopixel] = (100, 100, 100)
            elif (key_event.key_number == 8) and key_event.pressed:
                self.midi_panic()  # Play button kills all active MIDI notes
            elif (key_event.key_number == 9) and key_event.pressed:
                pass  # TODO Implement function key to shift function of encoder knobs
            elif (key_event.key_number == 10) and key_event.pressed:  # Select Button
                machine.go_to_state("menu")
                return
            elif (key_event.key_number == 11) and key_event.pressed:  # Volume Button
                print("TODO: Decide what the volume button does")

            neopixels.show()
        self.poll_encoders()
