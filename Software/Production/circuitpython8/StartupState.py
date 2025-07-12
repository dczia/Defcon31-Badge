import time
import terminalio
from State import State
from adafruit_display_text import label
from setup import (
    display,
    keys,
    neopixels,
)


class StartupState(State):
    color = (0, 0, 0)
    timer = 0
    stage = 0

    @property
    def name(self):
        return "startup"

    def enter(self, machine):
        neopixels.fill((0, 0, 0))
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        self.color = (0, 0, 0)
        self.timer = 0
        self.stage = 0
        State.exit(self, machine)

    def update(self, machine):
        self.timer = self.timer + 1
        if self.stage == 0:
            text = "       DCZia\n  Electric Sampler"
            if len(text) > self.timer:
                text = text[0: self.timer]
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=5)
            display.show(text_area)
            self.color = (self.timer, self.timer, 0)
            if self.timer > (len(text) * 1.5):
                self.timer = 0
                self.stage = 1
        elif self.stage == 1:
            text = "Fueled by Green Chile\n     and Solder"
            if len(text) > self.timer:
                text = text[0: self.timer]
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=10)
            display.show(text_area)
            if self.timer > (len(text) * 1.5):
                self.timer = 0
                self.stage = 2
        else:
            if self.timer < (255 * 8):
                color = (0, self.timer % 255, 0)
                neopixels[self.timer // 255] = color
                neopixels.show()
                self.timer = self.timer + 1  # make it faster
            else:
                time.sleep(0.1)
                machine.go_to_state("menu")
        # Skip to menu if encoder is pressed
        key_event = keys.events.get()
        if key_event and key_event.pressed:
            machine.go_to_state("menu")
