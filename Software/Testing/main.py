import os
import board
import busio as io
import digitalio
import storage
import adafruit_sdcard
import microcontroller
from time import sleep
import audiocore
import board
import audiobusio


# Setup the SD card and mount it as /sd
spi = io.SPI(board.GP10, board.GP11, board.GP12)
cs = digitalio.DigitalInOut(board.GP13)
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# Setup audio
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
wave_file = open("/sd/StreetChicken.wav", "rb");
wav = audiocore.WaveFile(wave_file)


while True:
    print("Playing wave file")
    audio.play(wav)
    while audio.playing:
        pass
    print("Done!")
    sleep(5)
    