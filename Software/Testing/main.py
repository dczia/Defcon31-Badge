from setup import *
from os import listdir
import os
import displayio
import terminalio
from adafruit_display_text import label
import time
from supervisor import ticks_ms
import board
import busio as io
import audiobusio
import audiocore
import audiomixer
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase


# Setup audio
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
num_voices = 1
mixer = audiomixer.Mixer(voice_count=num_voices, sample_rate=22050, channel_count=1, bits_per_sample=16, samples_signed=True)
mixer.voice[0].level = .2
wave_file = open('/sd/StreetChicken.wav', 'rb')
wav = audiocore.WaveFile(wave_file)



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
        wave_file = open(self.fname, 'rb');
        #wav = audiocore.WaveFile(wave_file)
        
        seq_loop = True
        while seq_loop == True:
            # Helpful output for troubleshooting
            #print('Step ' + str(step) + ': ' + str(self.sequence[step][0]) + ', ' + str(self.sequence[step][1]))

            # Play notes that are set to true in seq array
            if self.sequence[step][0] == True:
                wav = audiocore.WaveFile(wave_file)

                # Set volume based on 'velocity' parameter
                mixer.voice[0].level = self.sequence[step][1]
                mixer.voice[0].play(wav)

            # Wait for beat duration and watch for stop
            while ticks_ms() < step_end:
                key_event = keys.events.get()
                if key_event and key_event.pressed:
                    if audio.playing == True:
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



# MIDI Functions
def send_note_on(note, octv):
    note = ((note)+(12*octv))
    midi_serial.send(NoteOn(note, 120))

def send_note_off(note, octv):
    note = ((note)+(12*octv))
    midi_serial.send(NoteOff(note, 0))

def send_cc(number, val):
    midi_serial.send(ControlChange(number, val))

# Menu Functions
def get_files():
    """ Get a list of Python files in the root folder of the Pico """
    
    files = listdir()
    menu = []
    for file in files:
        if file.endswith(".py"):
            menu.append(file)

    return(menu)

def show_menu(menu):
    """ Shows the menu on the screen"""
    
    display_group = displayio.Group()
    # bring in the global variables
    global line, highlight, shift, list_length

    # menu variables
    item = 1
    line = 1

    color_bitmap = displayio.Bitmap(width, line_height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF # White

    # Shift the list of files so that it shows on the display
    list_length = len(menu)
    short_list = menu[shift:shift+total_lines]

    for item in short_list:
        if highlight == line:
            white_rectangle = displayio.TileGrid(color_bitmap,
                               pixel_shader=color_palette,
                               x=0, y=((line-1)*line_height))
            display_group.append(white_rectangle)
            text_arrow = '>'
            text_arrow = label.Label(terminalio.FONT, text=text_arrow, color=0x000000, x=0, y=((line-1)*line_height)+offset)
            display_group.append(text_arrow)
            text_item = label.Label(terminalio.FONT, text=item, color=0x000000, x=10, y=((line-1)*line_height)+offset)
            display_group.append(text_item)
        else:
            text_item = label.Label(terminalio.FONT, text=item, color = 0xFFFFFF, x=10, y=((line-1)*line_height)+offset)
            display_group.append(text_item)
        line += 1
    display.show(display_group)

def launch(filename):
    """ Launch the Python script <filename> """
    global file_list
    time.sleep(3)
    exec(open(filename).read())
    show_menu(file_list)

# Get the list of Python files and display the menu
file_list = get_files()
show_menu(file_list)

class State(object):
    def __init__(self):
        pass
    @property
    def name(self):
        return ''
    def enter(self, machine):
        pass
    def exit(self, machine):
        pass
    def update(self, machine):
        if switch.fell:
            machine.paused_state = machine.state.name
            machine.pause()
            return False
        return True

class StateMachine(object):

    def __init__(self):
        self.state = None
        self.states = {}
        self.last_enc1_pos = encoder_1.position
        self.paused_state = None

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]
        self.state.enter(self)

    def update(self):
        if self.state:
            self.state.update(self)

    # When pausing, don't exit the state
    def pause(self):
        self.state = self.states['paused']
        self.state.enter(self)

    # When resuming, don't re-enter the state
    def resume_state(self, state_name):
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]

'''
class PausedState(State):

    def __init__(self):
        self.switch_pressed_at = 0

    @property
    def name(self):
        return 'paused'

    def enter(self, machine):
        State.enter(self, machine)
        #self.switch_pressed_at = time.monotonic()
        if audio.playing:
            audio.pause()

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        if switch.fell:
            if audio.paused:
                audio.resume()
            machine.resume_state(machine.paused_state)
        elif not switch.value:
            if time.monotonic() - self.switch_pressed_at > 1.0:
                machine.go_to_state('raising')
'''

class StartupState(State):
  
    @property
    def name(self):
        return 'startup'

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        neopixels.fill((0,0,0))
        text = 'DCZia\nElectric Sampler'
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=5)
        display.show(text_area)
        time.sleep(2)
        text = 'Fueled by Green Chile\nand Solder'
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=10)
        display.show(text_area)
        time.sleep(2)
        # Code for any startup animations, etc.
        for i in range(0,8):
            neopixels[i] = (0,255,0)
            time.sleep(.2)
        neopixels.fill((255,0,0))
        time.sleep(.2)
        machine.go_to_state('menu')

class MenuState(State):

    last_position = 0

    @property
    def name(self):
        return 'menu'

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # Code for moving through menu and selecting mode
        mode_select = False
        mode = 'flashy'
        #text = '1. Flashy Mode'
        #text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        #display.show(text_area)
        rainbow = Rainbow(neopixels, speed = 0.1)
        global highlight, shift
        show_menu(file_list)
        while True:
            rainbow.animate()
            if self.last_position is not encoder_1.position:
                if encoder_1.position < self.last_position:
                    if highlight > 1:
                        highlight -= 1
                    else:
                        if shift > 0:
                            shift -= 1
                    print('> ' + file_list[highlight-1+shift])
                    #show_menu(file_list)
                else:
                    if highlight < total_lines:
                        highlight += 1
                    else:
                        if shift+total_lines < list_length:
                            shift += 1
                    print('> ' + file_list[highlight-1+shift])
                show_menu(file_list)
            self.last_position = encoder_1.position

            # Check for button pressed
            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                print("Button Pressed)")
                print("Launching", file_list[highlight-1+shift])

                # execute script
                launch(file_list[(highlight-1) + shift])
                print("Returned from launch")
        '''
        while mode_select is False:
            rainbow.animate()
            # Some code here to use an encoder to scroll through menu options, press to select one
            position = encoder_1.position

            if position > self.last_position:
                if mode == 'flashy':
                    mode = 'sequencer'
                    text = '2. Sequencer'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                elif mode == 'sequencer':
                    mode = 'sampler'
                    text = '3. Sampler'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                elif mode == 'sampler':
                    mode = 'midi_controller'
                    text = '4. MIDI Controller'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                elif mode == 'midi_controller':
                    mode = 'flashy'
                    text = '1. Flashy Mode'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
            if self.last_position > position:
                if mode == 'flashy':
                    mode = 'midi_controller'
                    text = '4. MIDI Controller'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                elif mode == 'sequencer':
                    mode = 'flashy'
                    text = '1. Flashy Mode'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                elif mode == 'sampler':
                    mode = 'sequencer'
                    text = '2. Sequencer'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                elif mode == 'midi_controller':
                    mode = 'sampler'
                    text = '3. Sampler'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
            self.last_position = position

            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                if mode == 'sequencer':
                    machine.go_to_state('sequencer')
                    mode_select = True
                if mode == 'sampler':
                    machine.go_to_state('sampler')
                    mode_select = True
                if mode == 'midi_controller':
                    machine.go_to_state('midi_controller')
                    mode_select = True
                if mode == 'flashy':
                    machine.go_to_state('flashy')
                    mode_select = True
        '''
class SequencerState(State):
  
    @property
    def name(self):
        return 'sequencer'

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # Sequencer code
        text = 'Sequencer'
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)
        run_sequencer = True
        while run_sequencer is True:
            #send_note_on(1,4)
            #time.sleep(1.5)
            #send_note_off(1,4)
            #time.sleep(1.5)
            #send_note_on(5,4)
            #time.sleep(1.5)
            #send_note_off(5,4)
            #time.sleep(1.5)
            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                run_sequencer = False
                machine.go_to_state('menu')

class SamplerState(State):
  
    @property
    def name(self):
        return 'sampler'

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # Sampler code
        text = 'Sampler'
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)
        sequencer_play = True

        # Pressing encoder will start looping the sequencer
        while sequencer_play == True:
            key_event = keys.events.get()
            if key_event and key_event.pressed:
                key = key_event.key_number
                if key == 0:
                    audio.play(mixer)
                    tracks = []
                    test = fileSequencer
                    test().set_sequence()
                    test().play_sequence()
            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                machine.go_to_state('menu')
                sequencer_play = False
                '''
                else:
                    print('exit')
                    machine.go_to_state('menu')
                    sequencer_play = False
                '''

class MIDIState(State):
  
    @property
    def name(self):
        return 'midi_controller'

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        text = 'MIDI Controller'
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)

        neopixels.fill((255,0,0))
        neopixels.show()
        run_midi = True
        while run_midi == True:
            key_event = keys.events.get()
            if key_event:
                if key_event.pressed:
                    key = key_event.key_number
                    send_note_on(key,4)
                    neopixels[key] = (0,0,255)
                    neopixels.show()

                if key_event.released:
                    key = key_event.key_number
                    send_note_off(key,4)
                    neopixels[key] = (255,0,0)
                    neopixels.show()

            enc_buttons_event = enc_buttons.events.get()
            enc_buttons.events.clear()
            if enc_buttons_event and enc_buttons_event.pressed:
                machine.go_to_state('menu')
                run_midi = False


class FlashyState(State):

    last_position = encoder_1.position

    @property
    def name(self):
        return 'flashy'

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        party = True
        choices = ["rainbow", "rainbow_chase"]
        i = 0
        selection = choices[i]
        text = 'Rainbow'
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)
        rainbow = Rainbow(neopixels, speed = 0.1)
        rainbow_chase = RainbowChase(neopixels, speed=0.1, size=5, spacing=3)
        while party is True:
            position = encoder_1.position
            if position > self.last_position:
                if i == len(choices):
                    i = 0
                selection = choices[i]
                i += 1
                if selection == 'rainbow':
                    text = 'Rainbow'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                    rainbow_chase.freeze()
                    rainbow.animate()
                if selection == 'rainbow_chase':
                    text = 'Rainbow Chase'
                    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
                    display.show(text_area)
                    rainbow.freeze()
                    rainbow_chase.animate()

            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                neopixels.fill((255,0,0))
                neopixels.show()
                machine.go_to_state('menu')
                party = False


machine = StateMachine()
machine.add_state(StartupState())
machine.add_state(MenuState())
machine.add_state(SequencerState())
machine.add_state(SamplerState())
machine.add_state(MIDIState())
machine.add_state(FlashyState())

machine.go_to_state('startup')

while True:
    machine.update()


