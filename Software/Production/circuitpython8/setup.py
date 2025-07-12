import adafruit_displayio_ssd1306
import adafruit_midi
import adafruit_sdcard
import board
import busio
import digitalio
import displayio
import keypad
import neopixel
import rotaryio
import storage
import terminalio
import time
import usb_midi

from adafruit_display_text import label

# OLED Screen ( display )
displayio.release_displays()
i2c = busio.I2C(board.GP15, board.GP14)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)

# Neopixels
neopixels = neopixel.NeoPixel(board.GP3, 10, brightness=0.1, auto_write=True)

# Board LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Sync Out
sync_out = digitalio.DigitalInOut(board.GP7)
sync_out.direction = digitalio.Direction.OUTPUT

# Sync In
sync_in = digitalio.DigitalInOut(board.GP6)
sync_in.direction = digitalio.Direction.INPUT

# Buttons
# 0-7 Buttons
# 8 Play
# 9 Function
# 10 Select
# 11 Volume
keys = keypad.KeyMatrix(
    row_pins=(board.GP27, board.GP26, board.GP18),
    column_pins=(board.GP20, board.GP21, board.GP22, board.GP28),
    columns_to_anodes=False,
)

# Setup rotary encoders
select_enc = rotaryio.IncrementalEncoder(board.GP16, board.GP17)
volume_enc = rotaryio.IncrementalEncoder(board.GP4, board.GP5)

# MIDI setup
midi_uart = busio.UART(tx=board.GP8, baudrate=31250)
midi_serial_channel = 1
midi_serial = adafruit_midi.MIDI(
    midi_out=midi_uart, out_channel=midi_serial_channel - 1
)

midi_usb = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1], out_channel=0
)

# Setup the SD card and mount it as /sd
try:
    # busio.SPI(clock:, MOSI: , MISO:)
    spi = busio.SPI(board.GP10, board.GP11, board.GP12)
    cs = digitalio.DigitalInOut(board.GP13)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except:
    text = "No SD Card Found!"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
    display.show(text_area)
    time.sleep(5)
