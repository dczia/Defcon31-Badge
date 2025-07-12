from adafruit_led_animation.animation.rainbow import Rainbow

from State import State
from utils import show_menu
from setup import (
    neopixels,
    select_enc,
    keys,
)


class MenuState(State):
    menu_items = [
        {
            "name": "flashy",
            "pretty": "Flashy",
        },
        {
            "name": "sampler_menu",
            "pretty": "Sampler",
        },
        {
            "name": "sequencer_menu",
            "pretty": "Sequencer",
        },
        {
            "name": "midi_controller",
            "pretty": "MIDI Controller",
        },
        {
            "name": "hid",
            "pretty": "USB HID Mode",
        },
        {
            "name": "startup",
            "pretty": "Startup State (test)",
        },
    ]

    @property
    def name(self):
        return "menu"

    def __init__(self):
        self.total_lines = 3
        self.list_length = len(self.menu_items)
        self.highlight = 1
        self.shift = 0

    def enter(self, machine):
        self.last_position = 0
        if machine.animation is None:
            machine.animation = Rainbow(neopixels, speed=0.1)
        show_menu(self.menu_items, self.highlight, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        select_enc.position = 0
        State.exit(self, machine)

    def update(self, machine):
        # Code for moving through menu and selecting mode
        if machine.animation:
            machine.animation.animate()
        # Some code here to use an encoder to scroll through menu options, press to select one
        position = select_enc.position

        if self.last_position != position:
            if position < self.last_position:
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
        self.last_position = position

        key = keys.events.get()
        if key and key.pressed:
            machine.go_to_state(
                self.menu_items[self.highlight - 1 + self.shift]["name"]
            )
