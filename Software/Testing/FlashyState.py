import terminalio

from adafruit_display_text import label
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.sparklepulse import SparklePulse

from state import State

from setup import (
    display,
    enc_buttons,
    encoder_1,
    neopixels,
)


class FlashyState(State):
    animation = False

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

    def enter(self, machine):
        self.last_position = -4096
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        neopixels.show()
        encoder_1.position = 0
        State.exit(self, machine)

    def update(self, machine):
        position = encoder_1.position
        if position != self.last_position:
            index = position % len(
                self.menu_items
            )  # Generate a valid index from the position
            pretty_name = self.menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            text_area = label.Label(
                terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
            )
            display.show(text_area)
            self.last_position = position
            if self.menu_items[index]["function"] == "rainbow":
                self.animation = Rainbow(neopixels, speed=0.1)
            elif self.menu_items[index]["function"] == "rainbow_chase":
                self.animation = RainbowChase(neopixels, speed=0.1)
            elif self.menu_items[index]["function"] == "rainbow_comet":
                self.animation = RainbowComet(neopixels, speed=0.1, tail_length=10)
            elif self.menu_items[index]["function"] == "rainbow_sparkle":
                self.animation = RainbowSparkle(
                    neopixels, speed=0.1, period=5, num_sparkles=None, step=1
                )
            elif self.menu_items[index]["function"] == "sparkle_pulse":
                self.animation = SparklePulse(
                    neopixels,
                    speed=0.1,
                    color=(0, 255, 0),
                    period=5,
                    max_intensity=1,
                    min_intensity=0,
                )
        else:
            # All animations need to impliment animate() as their step function
            if self.animation and self.animation.animate:
                self.animation.animate()

        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state("menu")
