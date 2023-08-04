import board
import busio as io
import digitalio
import storage
import adafruit_sdcard
import audiocore
import audiobusio
import rotaryio
import audiomixer
import time
import adafruit_midi
import neopixel
import displayio
import adafruit_displayio_ssd1306
import keypad
import terminalio
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


# Board LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Neopixels
#pixel_pin = board.GP28
#num_pixels = 8
#neopixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.5, #auto_write=True)

# Sync Out
sync_out = digitalio.DigitalInOut(board.GP7)
sync_out.direction = digitalio.Direction.OUTPUT

# Sync In
sync_in = digitalio.DigitalInOut(board.GP6)
sync_in.direction = digitalio.Direction.INPUT

# Setup Keyswitch Matrix
matrix = keypad.KeyMatrix(
    row_pins=(board.GP27, board.GP26, board.GP18),
    column_pins=(board.GP20, board.GP21, board.GP22, board.GP28),
    columns_to_anodes=False,
)

# Setup rotary encoders
enc_volume = rotaryio.IncrementalEncoder(board.GP4, board.GP5)
enc_select = rotaryio.IncrementalEncoder(board.GP16, board.GP17)

# MIDI setup
midi_uart = io.UART(rx=board.GP9, tx=board.GP8, baudrate=31250)
midi_serial_channel = 1
midi_serial = adafruit_midi.MIDI(
    midi_out=midi_uart, out_channel=midi_serial_channel - 1
)

# Setup the SD card and mount it as /sd
try:
    spi = io.SPI(board.GP10, board.GP11, board.GP12)
    cs = digitalio.DigitalInOut(board.GP13)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except:
    text = "SD Card Failed!"
    text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
    display.show(text_area)
    time.sleep(10)

# Setup audio
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
num_voices = 10
mixer = audiomixer.Mixer(
    voice_count=num_voices,
    sample_rate=16000,
    channel_count=1,
    bits_per_sample=16,
    samples_signed=True,
)
time.sleep(0.1)
mixer.voice[0].level = 0.5  # volume
time.sleep(0.1)
text = "Audio Test"
text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
display.show(text_area)
# Load wav file
wave_file = open("/samples/Snare.wav", "rb")
wav = audiocore.WaveFile(wave_file)
time.sleep(0.1)
audio.play(mixer)
for count in range(0, 5):
    mixer.voice[0].play(wav)
    while mixer.voice[0].playing:
        pass
audio.stop()



def cycle_neopixels():
    text = "Neopixel Test"
    text_area = label.Label(terminalio.FONT, text=text, color=0x00FFFF, x=2, y=15)
    display.show(text_area)

    neopixels.fill((255, 0, 0))
    neopixels.show()
    time.sleep(1)
    neopixels.fill((0, 255, 0))
    neopixels.show()
    time.sleep(1)
    neopixels.fill((0, 0, 255))
    neopixels.show()
    time.sleep(1)
    neopixels.fill((255, 255, 255))
    neopixels.show()
    time.sleep(1)
    neopixels.fill((0, 0, 0))
    neopixels.show()
    time.sleep(1)


def switch_check():
    text = "Switch Test"
    text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
    display.show(text_area)
    cycle = False
    sel_last_pos = enc_select.position
    vol_last_pos = enc_volume.position
    while cycle is False:
        event = matrix.events.get()
        if event:
            text = str(event)
            text_area = label.Label(
                terminalio.FONT, text=text, x=2, y=15
            )
            display.show(text_area)
            key = event.key_number
            if key == 11:
                cycle = True
        if vol_last_pos != enc_volume.position:
            text = str(f"Volume: {enc_volume.position}")
            text_area = label.Label(
                terminalio.FONT, text=text, x=2, y=15
            )
            display.show(text_area)
            vol_last_pos = enc_volume.position
        if sel_last_pos != enc_select.position:
            text = str(f"Select: {enc_select.position}")
            text_area = label.Label(
                terminalio.FONT, text=text, x=2, y=15
            )
            display.show(text_area)
            sel_last_pos = enc_select.position


while True:
    #cycle_neopixels()
    switch_check()

