import terminalio
import displayio
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


# Define scales for future update
# scale_dict = {
# "Major":[0, 2, 4, 5, 7, 9, 11, 12],
# "Minor":[0, 2, 3, 5, 7, 8, 10, 12],
# "Dorian":[0, 2, 3, 5, 7, 9, 10, 12],
# "Phrygian:":[0, 1, 3, 5, 7, 8, 10, 12],
# "Locrian":[0, 1, 3, 5, 6, 8, 10, 12],
# "Lydian":[0, 2, 4, 6, 7, 9, 11, 12],
# }

def get_note_name(midi_value):
    notes = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab","A", "A#/Bb", "B"]
    note = midi_value % 12
    octave = (midi_value // 12) - 1
    return(notes[note], str(octave))
    
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

    def update_screen(self):
        note_text, octave_text = get_note_name(self.base)
        text = "MIDI Controller\n" + note_text + octave_text + " " + self.current_scale
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=8)
        display.root_group = text_area

    def enter(self, machine):
        #text = "MIDI Controller"
        #text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
        #display.root_group = text_area
        neopixels.fill((100, 100, 100))
        neopixels.show()
        # Reset encoder positions
        select_enc.position = 0
        volume_enc.position = 0
        self.last_select_position = select_enc.position
        self.last_volume_position = volume_enc.position
        self.notes = []  # Current pressed notes
        self.scale = []  # Current scale
        self.base = 24  # Current base note
        self.current_scale = "Major"
        self.generate_major_scale(self.base)
        self.update_screen()
        self.function_key = False
        #display.root_group = display_group
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
        # Alternate function while holding function key
        if self.function_key is True:
            # Check volume knob
            if volume_enc.position != self.last_volume_position:
                if volume_enc.position < self.last_volume_position:
                    # Shift base note down
                    self.base_down()
                elif volume_enc.position > self.last_volume_position:
                    # Shift base note up
                    self.base_up()
                if self.current_scale == "Major":
                    self.generate_major_scale(self.base)

                elif self.current_scale == "Minor":
                    self.generate_minor_scale(self.base)

                self.last_volume_position = volume_enc.position
                self.update_screen()

        # Function key not held down
        else:
            # Check select knob
            if select_enc.position != self.last_select_position:
                if select_enc.position < self.last_select_position:
                    self.octave_down()
                elif select_enc.position > self.last_select_position:
                    self.octave_up()

                self.last_select_position = select_enc.position
                self.update_screen()

            # Check volume knob
            if volume_enc.position != self.last_volume_position:
                # Change to minor if already major
                if self.current_scale == "Major":
                    self.generate_minor_scale(self.base)
                    self.current_scale = "Minor"

                # Change to major if already minor
                elif self.current_scale == "Minor":
                    self.generate_major_scale(self.base)
                    self.current_scale = "Major"

                self.last_volume_position = volume_enc.position
                self.update_screen()

    def update(self, machine):
        # Listen on USB MIDI, resolves issues with some software
        # TODO Make this more elegant
        midi_usb.receive()
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
                self.function_key = True
            elif (key_event.key_number == 9) and key_event.released:
                self.function_key = False
            elif (key_event.key_number == 10) and key_event.pressed:  # Select Button
                machine.go_to_state("menu")
                return
            elif (key_event.key_number == 11) and key_event.pressed:  # Volume Button
                print("TODO: Decide what the volume button does")

            neopixels.show()
        self.poll_encoders()
