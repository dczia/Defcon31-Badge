import board
import busio as io
import digitalio
import storage
import adafruit_sdcard
import time
# import microcontroller
# import audiocore
import audiobusio
import rotaryio
import keypad
import neopixel
import adafruit_midi
import usb_midi

# Display imports
import displayio
import terminalio
import adafruit_displayio_ssd1306
from adafruit_display_text import label

# Setup I/O

# OLED Screen
displayio.release_displays()
i2c = io.I2C(board.GP15, board.GP14)
width = 128
height = 32
line = 1
line_height = 10
offset = 5
highlight = 1
shift = 0
list_length = 0
total_lines = 3
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=width, height=height)

# Neopixels
pixel_pin = board.GP28
num_pixels = 8
neopixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=True)

# Board LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Sync Out
sync_out = digitalio.DigitalInOut(board.GP9)
sync_out.direction = digitalio.Direction.OUTPUT

# Sync In
sync_in = digitalio.DigitalInOut(board.GP6)
sync_in.direction = digitalio.Direction.INPUT

# Encoder buttons (GP16 is unassigned, but keys wants multiple inputs)
enc_pins = [board.GP3]
enc_buttons = keypad.Keys(enc_pins, value_when_pressed=False, pull=True)

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

# ON_COLOR = (0, 0, 255)
# OFF_COLOR = (255, 0, 0)

keys = keypad.Keys(keyswitch_pins, value_when_pressed=False, pull=True)
# neopixels.fill(OFF_COLOR)

# Setup rotary encoders
encoder_1 = rotaryio.IncrementalEncoder(board.GP4, board.GP5)

# for tracking the direction and button state
previous_value = True
button_down = False

# MIDI setup
midi_uart = io.UART(tx=board.GP8, baudrate=31250)
midi_serial_channel = 2
midi_serial = adafruit_midi.MIDI(
    midi_out=midi_uart, out_channel=midi_serial_channel - 1
)

midi_usb = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0)

# Setup the SD card and mount it as /sd
try:
    spi = io.SPI(board.GP10, board.GP11, board.GP12)
    cs = digitalio.DigitalInOut(board.GP13)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except:
    text = "No SD Card Found!"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
    display.show(text_area)
    time.sleep(5)

# Setup audio
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
# volume
