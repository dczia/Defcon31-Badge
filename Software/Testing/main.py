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
import rotaryio
import audiomixer
import time
from supervisor import ticks_ms

# Set one test case to true to test function
test_midi = False
test_seq = True


#MIDI Imports
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.pitch_bend import PitchBend

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# MIDI setup (add rx=board.GP9 on next hw rev)
# Todo: Implement MIDI over USB
midi_uart = io.UART(tx=board.GP8, baudrate=31250) # timeout=midi_timeout)
midi_serial_channel = 2
midi_serial = adafruit_midi.MIDI(midi_out=midi_uart, out_channel=midi_serial_channel-1)


def send_note_on(note, octv):
    note = ((note)+(12*octv))
    midi_serial.send(NoteOn(note, 120))

def send_note_off(note, octv):
    note = ((note)+(12*octv))
    midi_serial.send(NoteOff(note, 0))

def send_cc(number, val):
    midi_serial.send(ControlChange(number, val))


# Setup the SD card and mount it as /sd
spi = io.SPI(board.GP10, board.GP11, board.GP12)
cs = digitalio.DigitalInOut(board.GP13)
sdcard = adafruit_sdcard.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# Setup audio
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)


num_voices = 1
mixer = audiomixer.Mixer(voice_count=num_voices, sample_rate=22050, channel_count=1, bits_per_sample=16, samples_signed=True)

mixer.voice[0].level = 0.5  # volume

# Setup rotary encoder
encoder = rotaryio.IncrementalEncoder(board.GP4, board.GP5)
button = digitalio.DigitalInOut(board.GP3)
last_knob_pos = encoder.position
last_enc_button = button.value

# Check for change on encoder knob
def pollKnob(last_knob_Pos):
    # poll knob
    change = encoder.position - last_knob_pos
    if change > 0:
        return 1,encoder.position
    elif change < 0:
        return -1,encoder.position
    elif change == 0:
        return 0,encoder.position

# Check for change on encoder button
def pollEncButton(last_enc_button):
    if button.value != last_enc_button:
        lastEncButton = button.value
        return 1,button.value   
    else:
        return 0,button.value

# Adjust volume
# value or 1 raises volume, -1 lowers volume
def changeVolume(volDirection):
    if volDirection > 0:
        if mixer.voice[0].level < 0.95:
            mixer.voice[0].level = mixer.voice[0].level + 0.05
        else:
            mixer.voice[0].level = 1
    elif volDirection < 0:
        if mixer.voice[0].level > 0.05:
            mixer.voice[0].level = mixer.voice[0].level - 0.05
        else:
            mixer.voice[0].level = 0
    print('Volume: ' + str(mixer.voice[0].level))


class MyClass:
    def __init__(self):
        self.clk_src = 'int'
    """A simple example class"""

    def f(self):
        return 'hello world'
test = MyClass
print(test().clk_src)

# File sequencer class
# Sets up a sequence track to play a .wav file sample at regular intervals
# 8 step sequence tells whether to play  
class fileSequencer:
    def __init__(self):
        self.clk_src = 'int'
        self.bpm = 120
        self.fname = '/sd/StreetChicken.wav'
        self.sequence = [[True, 1],[False, 0],[True, .2],[False, 0],[True, .4],[False, 0],[True, 1],[False, 0]]

    def select_file(self):
        # Show valid files, select with encoder knob/button
        print('valid files: ' + str(os.listdir()))
        fname = 'kick.wav'

        self.fname = fname
    def set_bpm(self):
        # Display bpm on screen, select with enc knob/button
        screen_input = 120
        self.bpm = screen_input

    # Set and store a sequence with True/False indicating steps to play on and int being a velocity value between 0-1
    def set_sequence(self):
        # Enter sequence mode, set with keys, exit with encoder
        key_input = [[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0],[False, 0]]
        self.sequence = key_input

    # Velocity will affect playback volume of a given sample in the sequence to add more movement to the sound
    def set_velocity(self):
        # Display current vel setting on screen and flash sequence step
        # Use encoder to select volume, and press to advance
        pass

    def set_clk_src(self):
        clk_options = ['ext, midi, int']
        # Display clk_options on screen, scroll/select
        # Ext takes signal from sync in, midi syncs to midi input, int is
        # internally clocked
        if clk_src == 'ext':
            print('need to implement')
        elif clk_src == 'midi':
            print('need to implement')
        elif clk_src == 'int':
            pass

    def play_sequence(self):
        # Calculate time for step
        step_length = int(1000 // (self.bpm / 60))
        step_start = ticks_ms()
        step = 0
        step_end = step_start + step_length
        # Load wav file
        wave_file = open(self.fname, "rb");
        #wav = audiocore.WaveFile(wave_file)
        
        seq_loop = True
        while seq_loop == True:
            # Helpful output for troubleshooting
            print('Step ' + str(step) + ': ' + str(self.sequence[step][0]) + ', ' + str(self.sequence[step][1]))

            # Play notes that are set to true in seq array
            if self.sequence[step][0] == True:
                wav = audiocore.WaveFile(wave_file)

                # Set volume based on 'velocity' parameter
                mixer.voice[0].level = self.sequence[step][1]
                mixer.voice[0].play(wav)

            # Wait for beat duration and poll for encoder press for pause
            # Encoder polling is pretty jank, need to improve
            while ticks_ms() < step_end:
                change,last_enc_button = pollEncButton(False) #last_enc_button)
                if change != 0 and last_enc_button == False:
                    if audio.playing == True:
                        print('stop')
                        audio.stop()
                        seq_loop = False

            # End audio at end of beat duration
            mixer.voice[0].stop()

            # Increment step and restart sequence if needed
            if step < 7:
                step +=1
            else:
                step = 0
            step_start = step_end
            step_end = step_start + step_length

test_midi = False
test_seq = True

# Test midi output
# Test should alternate between two notes every 1.5s
if test_midi == True:
    while True:
        send_note_on(1,4)
        time.sleep(1.5)
        send_note_off(1,4)
        time.sleep(1.5)
        send_note_on(5,4)
        time.sleep(1.5)
        send_note_off(5,4)
        time.sleep(1.5)

# Test sequencer output
# Pressing encoder will start looping the sequencer
if test_seq == True:
    while True:
        change,last_knob_pos = pollKnob(last_knob_pos)
        if change != 0:
            changeVolume(change)
        change,last_enc_button = pollEncButton(last_enc_button)
        if change != 0 and last_enc_button == False:
            if audio.playing == True:
                print('stop')
                audio.stop()
            else:
                audio.play(mixer)
                tracks = []
                test = fileSequencer
                test().set_sequence()
                test().play_sequence()

