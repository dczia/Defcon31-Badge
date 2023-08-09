import terminalio
import usb_hid
from adafruit_display_text import label
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from setup import (
    display,
    keys,
    neopixels,
    select_enc,
    volume_enc,
)
from utils import (
    neoindex,
)

from State import State


class HIDState(State):
    keymap = [
        Keycode.KEYPAD_ONE,
        Keycode.KEYPAD_TWO,
        Keycode.KEYPAD_THREE,
        Keycode.KEYPAD_FOUR,
        Keycode.KEYPAD_FIVE,
        Keycode.KEYPAD_SIX,
        Keycode.KEYPAD_SEVEN,
        Keycode.KEYPAD_EIGHT,
        Keycode.KEYPAD_NINE,
        Keycode.KEYPAD_ZERO,
        Keycode.KEYPAD_NINE,
        Keycode.KEYPAD_ZERO,
    ]

    @property
    def name(self):
        return "hid"

    def __init__(self):
        try:
            self.kbd = Keyboard(usb_hid.devices)
            self.consumer_control = ConsumerControl(usb_hid.devices)
        except:
            # Dummy functions when we aren't plugged into a computer
            class fakekb:
                def press(self, foo):
                    print("No keyboard:", foo)

                def release(self, foo):
                    print("No keyboard:", foo)

                def send(self, foo):
                    print("No keyboard:", foo)

            self.kbd = fakekb()
            self.consumer_control = fakekb()

    def enter(self, machine):
        text = "HID Controller"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
        display.show(text_area)
        neopixels.fill((100, 100, 100))
        neopixels.show()
        select_enc.position = 0
        volume_enc.position = 0
        self.volume_position = 0
        self.select_position = 0
        State.enter(self, machine)

    def exit(self, machine):
        select_enc.position = 0
        volume_enc.position = 0
        State.exit(self, machine)

    def update(self, machine):
        cur_position = volume_enc.position
        if cur_position != self.volume_position:
            if cur_position > self.volume_position:
                self.consumer_control.send(ConsumerControlCode.VOLUME_INCREMENT)
            else:
                self.consumer_control.send(ConsumerControlCode.VOLUME_DECREMENT)
            print(self.volume_position)
            print(cur_position)
            self.volume_position = cur_position

        cur_position = select_enc.position
        if cur_position != self.select_position:
            if cur_position > self.select_position:
                self.kbd.press(Keycode.KEYPAD_PLUS)
                self.kbd.release(Keycode.KEYPAD_PLUS)
            else:
                self.kbd.press(Keycode.KEYPAD_MINUS)
                self.kbd.release(Keycode.KEYPAD_MINUS)
            print(self.select_position)
            print(cur_position)
            self.select_position = cur_position
        #
        # Handle keyswitches
        #
        key_event = keys.events.get()
        while key_event:
            if key_event.key_number < 10:
                if key_event.pressed:
                    self.kbd.press(self.keymap[key_event.key_number])
                    mapped_neopixel = neoindex(key_event.key_number)
                    neopixels[mapped_neopixel] = (255, 0, 0)
                if key_event.released:
                    self.kbd.release(self.keymap[key_event.key_number])
                    mapped_neopixel = neoindex(key_event.key_number)
                    neopixels[mapped_neopixel] = (100, 100, 100)
            elif (key_event.key_number == 10) and key_event.pressed:  # Select Button
                machine.go_to_state("menu")
                return
            elif (key_event.key_number == 11) and key_event.pressed:  # Volume Button
                self.consumer_control.send(ConsumerControlCode.MUTE)

            key_event = keys.events.get()
        neopixels.show()
