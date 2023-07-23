#
# Example of USB HID input from the badge
#
import adafruit_displayio_ssd1306
import board
import busio as io
import digitalio
import displayio
import keypad
import neopixel
import rotaryio
import usb_hid

from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

#
# Intialize everything as normal
#

print("Starting")
# OLED Screen
displayio.release_displays()
i2c = io.I2C(board.GP15, board.GP14)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)

# Board LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Encoder buttons (GP16 is unassigned, but keys wants multiple inputs)
enc_1 = rotaryio.IncrementalEncoder(board.GP4, board.GP5)
enc_1_pins = [board.GP3]
enc_1_buttons = keypad.Keys(enc_1_pins, value_when_pressed=False, pull=True)


# Set up keys
keyswitch_pins = (
    board.GP27,
    board.GP26,
    board.GP22,
    board.GP21,
    board.GP20,
    board.GP19,
    board.GP18,
    board.GP17,
)
keys = keypad.Keys(keyswitch_pins, value_when_pressed=False, pull=True)

# Neopixels
pixel_pin = board.GP28
num_pixels = 8
neopixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.01)
neopixels.fill((255, 255, 255))

# Generate keyboard for keyboard keys and consumer control for volume controls
kbd = Keyboard(usb_hid.devices)
consumer_control = ConsumerControl(usb_hid.devices)

# Map each button index to a numpad number
keymap = [
    Keycode.KEYPAD_ZERO,
    Keycode.KEYPAD_ONE,
    Keycode.KEYPAD_TWO,
    Keycode.KEYPAD_THREE,
    Keycode.KEYPAD_FOUR,
    Keycode.KEYPAD_FIVE,
    Keycode.KEYPAD_SIX,
    Keycode.KEYPAD_SEVEN,
    Keycode.KEYPAD_EIGHT,
]


def press_key(key_number):
    kbd.press(keymap[key_number])


def release_key(key_number):
    kbd.release(keymap[key_number])


enc_1_position = 0
while True:
    #
    # Handle encode knob inputs
    #
    cur_position = enc_1.position
    if cur_position != enc_1_position:
        if cur_position > enc_1_position:
            print("Encoder increased")
            consumer_control.send(ConsumerControlCode.VOLUME_INCREMENT)
        else:
            print("Encoder decreased")
            consumer_control.send(ConsumerControlCode.VOLUME_DECREMENT)
    #
    # Handle encoder button
    #
    enc_1_buttons_event = enc_1_buttons.events.get()
    if enc_1_buttons_event:
        if enc_1_buttons_event.pressed:
            print("Encoder pressed")
            consumer_control.send(ConsumerControlCode.MUTE)
        if enc_1_buttons_event.released:
            print("Encoder released")
    #
    # Handle keyswitches
    #
    key_event = keys.events.get()
    if key_event:
        if key_event.pressed:
            print("Key pressed:", key_event.key_number)
            press_key(key_event.key_number)
            neopixels[key_event.key_number] = (255, 0, 0)
        if key_event.released:
            print("Key released:", key_event.key_number)
            release_key(key_event.key_number)
            neopixels[key_event.key_number] = (255, 255, 255)
    enc_1_position = cur_position
