from State import State
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.sparklepulse import SparklePulse
from utils import show_menu
from setup import (
    keys,
    neopixels,
    select_enc,
)


class FlashyState(State):
    menu_items = [
        {
            "function": "rainbow",
            "pretty": "Rainbow",
        },
        {
            "function": "rainbow_chase",
            "pretty": "Rainbow Chase",
        },
        {
            "function": "rainbow_comet",
            "pretty": "Rainbow Comet",
        },
        {
            "function": "rainbow_sparkle",
            "pretty": "Rainbow Sparkle",
        },
        {
            "function": "sparkle_pulse",
            "pretty": "Sparkle Pulse",
        },
    ]

    @property
    def name(self):
        return "flashy"

    def __init__(self):
        self.total_lines = 3
        self.list_length = len(self.menu_items)
        self.highlight = 1
        self.shift = 0

    def enter(self, machine):
        self.last_position = 0
        select_enc.position = 0
        show_menu(self.menu_items, self.highlight, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        neopixels.show()
        select_enc.position = 0
        State.exit(self, machine)

    def update(self, machine):
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
            selection = self.menu_items[self.highlight - 1 + self.shift]["function"]
            self.animation_selector(machine, selection)
        if machine.animation:
            machine.animation.animate()
        self.last_position = position
        key = keys.events.get()
        if key and key.pressed:
            machine.go_to_state("startup")  # TODO: change to menu

    def animation_selector(self, machine, name):
        if name == "rainbow":
            machine.animation = Rainbow(neopixels, speed=0.1)
        elif name == "rainbow_chase":
            machine.animation = RainbowChase(neopixels, speed=0.1)
        elif name == "rainbow_comet":
            machine.animation = RainbowComet(neopixels, speed=0.1, tail_length=10)
        elif name == "rainbow_sparkle":
            machine.animation = RainbowSparkle(
                neopixels, speed=0.1, period=5, num_sparkles=None, step=1
            )
        elif name == "sparkle_pulse":
            machine.animation = SparklePulse(
                neopixels,
                speed=0.1,
                color=(0, 255, 0),
                period=5,
                max_intensity=1,
                min_intensity=0,
            )
