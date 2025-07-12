import terminalio
from adafruit_display_text import label
from State import State
from adafruit_ticks import ticks_ms, ticks_add, ticks_less

from setup import (
    display,
    keys,
    neopixels,
    sync_in,
    select_enc,
    volume_enc,
)


# helper function for color changing
def color_wheel(value):
    if value < 85:
        color = (value * 3, 255 - value * 3, 0)
    elif value < 170:
        result = value - 85
        color = (255 - result * 3, 0, result * 3)
    else:
        result = value - 170
        color = (0, result * 3, 255 - result * 3)
    return color


class EyeCandyState(State):
    @property
    def name(self):
        return "eye_candy"

    def enter(self, machine):
        text = "Eye Candy"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
        display.root_group = text_area
        neopixels.fill((0, 0, 0))
        neopixels.show()
        # Reset encoder positions
        select_enc.position = 0
        volume_enc.position = 0
        self.last_select_position = select_enc.position
        self.last_volume_position = volume_enc.position
        self.seen_low = False
        self.color_index = 0
        self.level = 0
        self.fade_speed = 0.05
        self.brightness_scale = 0.2
        self.step_end = 0
        self.trigger_time = ticks_ms()
        keys.events.clear()
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((0, 0, 0))
        neopixels.show()
        State.exit(self, machine)

    def poll_encoders(self):
        # Check select knob
        if select_enc.position != self.last_select_position:
            if select_enc.position < self.last_select_position:
                self.fade_speed -= 0.01
            if select_enc.position > self.last_select_position:
                self.fade_speed += 0.01
            self.last_select_position = select_enc.position

        # Check volume knob
        if volume_enc.position != self.last_volume_position:
            # turn brightness down
            if volume_enc.position < self.last_volume_position:
                if self.brightness_scale > 0.02:
                    self.brightness_scale -= 0.02
                else:
                    self.brightness_scale = 0
            # turn brightness up
            if volume_enc.position > self.last_volume_position:
                if self.brightness_scale < 0.98:
                    self.brightness_scale += 0.02
                else:
                    self.brightness_scale = 1
            self.last_volume_position = volume_enc.position

    def update(self, machine):

        # cycle through a rainbow
        if self.color_index < 255:
            self.color_index += 1
        else:
            self.color_index = 0
        color = color_wheel(self.color_index)
        neopixels.fill(color)

        # check for trigger
        if sync_in.value is False:
            neopixels.brightness = 1 * self.brightness_scale
            # set time for light decay
            self.step_end = ticks_add(ticks_ms(), 10)
        # wait a bit between brightness checks
        if ticks_less(ticks_ms(), self.step_end):
            pass
        else:
            if neopixels.brightness > 0:
                neopixels.brightness -= self.fade_speed * self.brightness_scale
                self.step_end = ticks_add(ticks_ms(), 10)
            if neopixels.brightness < 0:
                neopixels.brightness = 0

        neopixels.show()

        self.poll_encoders()
        key = keys.events.get()
        if key and key.pressed:
            neopixels.brightness = 0.1
            machine.go_to_state("menu")
