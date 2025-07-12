import terminalio
import time
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_display_text import label
from State import State

from utils import (
    neoindex,
    show_menu,
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

# MIDI Functions

def send_cc(number, val):
    midi_serial.send(ControlChange(number, val))
    midi_usb.send(ControlChange(number, val))


class MIDICommandState(State):

    # Add this menu later to make it more user friendly
    '''
    device_menu = [
        {
            "name": "Moog Subharmonicon",
            "pretty": "moog_subharmonicon",
        },
        {
            "name": "MakeNoise 0-Coast",
            "pretty": "no_coast",
        },
    ]
    '''

    menu_items = [
        {
            "name": "sh_xor_on",
            "pretty": "XOR On",
        },
        {
            "name": "sh_xor_off",
            "pretty": "XOR Off",
        },
        {
            "name": "exit",
            "pretty": "Exit",
        },
    ]

    @property
    def name(self):
        return "midi_command"

    def __init__(self):
        self.total_lines = 3
        self.list_length = len(self.menu_items)
        self.highlight = 1
        self.shift = 0

    def enter(self, machine):
        text = "MIDI Commands"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
        display.show(text_area)
        neopixels.fill((100, 100, 100))
        neopixels.show()
        # Reset encoder positions
        select_enc.position = 0
        volume_enc.position = 0
        self.last_select_position = select_enc.position
        self.last_volume_position = volume_enc.position
        keys.events.clear()
        time.sleep(0.5)
        show_menu(self.menu_items, self.highlight, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        self.midi_panic()
        neopixels.fill((100, 100, 100))
        neopixels.show()
        State.exit(self, machine)

    def midi_panic(self):
        send_cc(123, 0)  # Turn off all MIDI signal
        self.notes = []

    def update(self, machine):
        selection = ""
        # Code for moving through menu and selecting mode
        if machine.animation:
            machine.animation.animate()
        # Some code here to use an encoder to scroll through menu options, press to select one
        select_position = select_enc.position

        if self.last_select_position != select_position:
            if select_position < self.last_select_position:
                if self.highlight > 1:
                    self.highlight -= 1
                else:
                    if self.shift > 0:
                        self.shift -= 1
            else:
                if self.highlight < self.total_lines:
                    self.highlight += 1
                else:
                    if self.shift + self.total_lines < self.list_length:
                        self.shift += 1
            show_menu(self.menu_items, self.highlight, self.shift)

        self.last_select_position = select_position

        key = keys.events.get()
        if key and key.pressed:
            selection = self.menu_items[self.highlight - 1 + self.shift]["name"]
            if selection == 'sh_xor_on':
                send_cc(113, 127)
                text = "XOR On"
                text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
                display.show(text_area)
                time.sleep(1)
                show_menu(self.menu_items, self.highlight, self.shift)
            elif selection == 'sh_xor_off':
                send_cc(113, 0)
                text = "XOR Off"
                text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
                display.show(text_area)
                time.sleep(1)
                show_menu(self.menu_items, self.highlight, self.shift)
            elif selection == 'exit':
                machine.go_to_state("menu")


