from setup import (
    neopixels,
    enc_buttons,
    display,
    encoder_1,
    midi_serial,
    total_lines,
    shift,
    highlight,
    line_height,
    width,
    offset,
    keys,
)
from os import listdir
import os
import displayio
import terminalio
from adafruit_display_text import label
import time
from supervisor import ticks_ms
import board
import audiobusio
import audiocore
import audiomixer
import usb_hid
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode


# Setup audio
audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
num_voices = 9
mixer = audiomixer.Mixer(
    voice_count=num_voices,
    sample_rate=16000,
    channel_count=1,
    bits_per_sample=16,
    samples_signed=True,
)

def menu_select(last_position, menu_items):
    item_selected = False
    while item_selected is False:
        current_position = encoder_1.position

        # Generate a valid index from the position
        if current_position != last_position:
            index = current_position % len(
                menu_items
            ) 
            pretty_name = menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            text_area = label.Label(
                terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
            )
            display.show(text_area)
            last_position = current_position

        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            index = current_position % len(menu_items)
            return(menu_items[index]["name"])

def sequence_selector(value, min_val, max_val, increment, key_val, encoder_pos):

    selection = True
    vel_change = False
    # Display current value
    while selection == True:
        text = f"Step {key_val}: {value[key_val][1]:.2f}"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=5)
        display.show(text_area)
        key_event = keys.events.get()

        # Modify value on encoder input
        if encoder_pos is not encoder_1.position:
            if encoder_1.position < encoder_pos:
                if value[key_val][1] > min_val + increment:
                    value[key_val][1] = value[key_val][1] - increment
                else:
                    value[key_val][1] = min_val

            else:
                if value[key_val][1] < max_val - increment:
                    value[key_val][1] = value[key_val][1] + increment
                else:
                    value[key_val][1] = max_val
            encoder_pos = encoder_1.position
            vel_change = True

        # Exit selection menu if key released
        if key_event and key_event.released:

            if key_event.key_number == key_val:
                if vel_change == False:
                    value[key_val][0] = not value[key_val][0]
                selection = False
    return encoder_pos


# File sequencer class
# Sets up a sequence track to play a .wav file sample at regular intervals
# 8 step sequence tells whether to play
class file_sequence:
    def __init__(self):
        self.fname = ""
        self.sequence = [
            [False, 0.5],
            [True, 0.5],
            [True, 0.5],
            [True, 0.5],
            [True, 0.5],
            [True, 0.5],
            [True, 0.5],
            [True, 0.5],
        ]

    def select_file(self):
        # Show valid files, select with encoder knob/button
        print("valid files: " + str(os.listdir()))
        fname = "kick.wav"
        self.fname = fname

    # Set and store a sequence with True/False indicating steps to play on and int being a velocity value between 0-1
    def set_sequence(self):
        # Enter sequence mode, set with keys, exit with encoder
        key_input = [
            [False, 0],
            [False, 0],
            [True, 0.5],
            [False, 0],
            [False, 0],
            [True, 0.5],
            [False, 0],
            [True, 0.5],
        ]
        self.sequence = key_input

    def show_sequence(self):
        for index, item in enumerate(self.sequence):
            if item[0] == True:
                neopixels[index] = (0, 0, 255)
            elif item[0] == False:
                neopixels[index] = (255, 0, 0)
            time.sleep(0.01)


class run_sequencer:
    def __init__(self):
        self.clk_src = "int"
        self.bpm = 120
        self.active_sequences = []
        self.sequence_step = 0
        self.wav_files = []
        self.loaded_wavs = []
        self.step = 0
        self.play_music = False

    # Add sequences to the active set
    def add_sequence(self, new_sequence):
        self.active_sequences.append(new_sequence)

    # Set BPM (needs integration with input, required)
    def set_bpm(self):
        # Display bpm on screen, select with enc knob/button
        screen_input = 120
        self.bpm = screen_input

    # Write sequence data to file to reload after power on/off (future)
    def save_sequence(self):
        pass

    # Load sequence from file to reload after power on/off (future)
    def load_sequence(self):
        pass

    ### Select where clock is coming from (not critical, but high priority nice-to-have)
    def set_clk_src(self):
        # clk_options = ["ext, midi, int"]
        # Display clk_options on screen, scroll/select
        # Ext takes signal from sync in, midi syncs to midi input, int is
        # internally clocked
        if clk_src == "ext":
            print("need to implement")
        elif clk_src == "midi":
            print("need to implement")
        elif clk_src == "int":
            pass

    def play_step(self):

        # Calculate step duration
        self.step_start = ticks_ms()
        self.step_end = self.step_start + self.step_length

        # Loop through active sequences and play indicated steps
        for index, item in enumerate(self.active_sequences):
            if item.sequence[self.step][0] == True:
                # Set volume based on input value
                mixer.voice[index].level = item.sequence[self.step][1]
                mixer.voice[index].play(self.loaded_wavs[index])

        # Cycle sequencer LED
        # neopixels[self.step] = (255,0,0)
        time.sleep(0.05)
        neopixels[self.step] = (0, 0, 255)

        # Wait for beat duration and watch for stop
        while ticks_ms() < self.step_end:

            ### Update to play/pause button for final hardware
            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                for index, item in enumerate(self.active_sequences):
                    mixer.voice[index].stop
                self.play_music = False

            # Stop output at end of step duration
            else:
                for index, item in enumerate(self.active_sequences):
                    mixer.voice[index].stop
        neopixels.fill((255, 0, 0))

    # Update step
    def step_update(self):
        if self.step < 7:
            self.step += 1
        else:
            self.step = 0

    def play_sequence(self):

        # Loop through active sequences and load wav files
        for item in self.active_sequences:

            # Load wav files to play
            self.wav_files.append(open(item.fname, "rb"))
            self.loaded_wavs.append(audiocore.WaveFile(self.wav_files[-1]))

        # Main sequencer loop
        # Calculate step duration
        self.step_length = int(1000 // (self.bpm / 60))

        self.play_music = True
        audio.play(mixer)
        while self.play_music == True:
            self.play_step()
            self.step_update()
        audio.stop()

# MIDI Functions
def send_note_on(note, octv):
    note = (note) + (12 * octv)
    midi_serial.send(NoteOn(note, 120))


def send_note_off(note, octv):
    note = (note) + (12 * octv)
    midi_serial.send(NoteOff(note, 0))


def send_cc(number, val):
    midi_serial.send(ControlChange(number, val))


# Menu Functions
def get_files():
    """Get a list of Python files in the root folder of the Pico"""

    files = listdir()
    menu = []
    for file in files:
        if file.endswith(".wav"):
            menu.append(file)

    return menu


def show_menu(menu):
    """Shows the menu on the screen"""

    display_group = displayio.Group()
    # bring in the global variables
    global line, highlight, shift, list_length

    # menu variables
    item = 1
    line = 1

    color_bitmap = displayio.Bitmap(width, line_height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    # Shift the list of files so that it shows on the display
    list_length = len(menu)
    short_list = menu[shift : shift + total_lines]

    for item in short_list:
        if highlight == line:
            white_rectangle = displayio.TileGrid(
                color_bitmap,
                pixel_shader=color_palette,
                x=0,
                y=((line - 1) * line_height),
            )
            display_group.append(white_rectangle)
            text_arrow = ">"
            text_arrow = label.Label(
                terminalio.FONT,
                text=text_arrow,
                color=0x000000,
                x=0,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_arrow)
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                color=0x000000,
                x=10,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_item)
        else:
            text_item = label.Label(
                terminalio.FONT,
                text=item,
                color=0xFFFFFF,
                x=10,
                y=((line - 1) * line_height) + offset,
            )
            display_group.append(text_item)
        line += 1
    display.show(display_group)


def launch(filename):
    """Launch the Python script <filename>"""
    global file_list
    time.sleep(3)
    exec(open(filename).read())
    show_menu(file_list)

class State(object):
    def __init__(self):
        pass

    @property
    def name(self):
        return ""

    def enter(self, machine):
        pass

    def exit(self, machine):
        pass

    def update(self, machine):
        # if switch.fell:
        #    machine.paused_state = machine.state.name
        #    machine.pause()
        #    return False
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
        self.state = self.states["paused"]
        self.state.enter(self)

    # When resuming, don't re-enter the state
    def resume_state(self, state_name):
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]


"""
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
"""


class StartupState(State):
    @property
    def name(self):
        return "startup"

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        neopixels.fill((0, 0, 0))
        text = "DCZia\nElectric Sampler"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=5)
        display.show(text_area)
        time.sleep(2)
        text = "Fueled by Green Chile\nand Solder"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=10)
        display.show(text_area)
        time.sleep(2)
        # Code for any startup animations, etc.
        for i in range(0, 8):
            neopixels[i] = (0, 255, 0)
            time.sleep(0.2)
        neopixels.fill((255, 0, 0))
        time.sleep(0.2)
        machine.go_to_state("menu")


class MenuState(State):
    menu_items = [
        {
            "name": "flashy",
            "pretty": "Flashy",
        },
        {
            "name": "sequencer",
            "pretty": "Sequencer",
        },
        {
            "name": "sampler",
            "pretty": "Sampler",
        },
        {
            "name": "midi_controller",
            "pretty": "MIDI Controller",
        },
        {
            "name": "hid",
            "pretty": "USB HID Mode",
        },
    ]

    @property
    def name(self):
        return "menu"

    def enter(self, machine):
        self.last_position = -4096
        self.rainbow = Rainbow(neopixels, speed=0.1)
        State.enter(self, machine)

    def exit(self, machine):
        encoder_1.position = 0
        State.exit(self, machine)

    def update(self, machine):
        # Code for moving through menu and selecting mode
        self.rainbow.animate()
        # Some code here to use an encoder to scroll through menu options, press to select one
        position = encoder_1.position

        if position != self.last_position:
            index = position % len(
                self.menu_items
            )  # Generate a valid index from the position
            # mode = self.menu_items[index]["name"]
            pretty_name = self.menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            text_area = label.Label(
                terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
            )
            display.show(text_area)
            self.last_position = position

        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            index = position % len(self.menu_items)
            machine.go_to_state(self.menu_items[index]["name"])


class SequencerState(State):
    @property
    def name(self):
        return "sequencer"

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        # Sequencer code
        text = "Sequencer"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)
        run_sequencer = True
        while run_sequencer is True:
            # send_note_on(1,4)
            # time.sleep(1.5)
            # send_note_off(1,4)
            # time.sleep(1.5)
            # send_note_on(5,4)
            # time.sleep(1.5)
            # send_note_off(5,4)
            # time.sleep(1.5)
            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                run_sequencer = False
                machine.go_to_state("menu")


class SamplerState(State):
    @property
    def name(self):
        return "sampler"

    def enter(self, machine):
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        ### Show menu text (Update with new menu)
        text = "Sampler"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)

        # Start sequencer
        ### Need to figure out a sensible place to move this to resolve scope issues


        ### Add menu and programming portions here
        ### Start menu emulating code
        selection = True
        while selection == True:
            text = "Add Dummy Sequences?\n Key1: yes, Key2: no"
            text_area = label.Label(
                terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
            )
            display.show(text_area)
            key_event = keys.events.get()
            if key_event and key_event.pressed:
                key = key_event.key_number
                if key == 0:
                    sequencer.add_sequence(file_sequence())
                    sequencer.active_sequences[0].fname = "Snare.wav"

                    sequencer.add_sequence(file_sequence())
                    sequencer.active_sequences[1].fname = "Tom.wav"
                    sequencer.active_sequences[1].set_sequence()

                    sequencer.add_sequence(file_sequence())
                    sequencer.active_sequences[2].fname = "Kick.wav"
                    sequencer.active_sequences[2].sequence = [
                        [True, 0.5],
                        [False, 0.5],
                        [True, 0.5],
                        [False, 0.5],
                        [True, 0.5],
                        [False, 0.5],
                        [True, 0.5],
                        [False, 0.5],
                    ]
                    selection = False
                if key == 1:
                    selection = False

        ### End menu emulating code

        text = "Sampler"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)
        
        # Show selection menu

        seq_menu_items = [
            {
                "name": "add_sequence",
                "pretty": "Add Sequence",
            },
            {
                "name": "edit_sequence",
                "pretty": "Edit Sequence",
            },
            {
                "name": "play_sequence",
                "pretty": "Play Sequence",
            },
        ]

        selection = menu_select(machine.last_enc1_pos, seq_menu_items)
        print(selection)
        if selection is 'add_sequence':
            # Display select file
            text = 'Select File'
            text_area = label.Label(
                terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
            )
            display.show(text_area)
            ### Add two lines of display, second line is file select

            enc_buttons_event = enc_buttons.events.get()
            if enc_buttons_event and enc_buttons_event.pressed:
                pass

        if selection == 'edit_sequence':
            editing_sequence = True
            while editing_sequence == True:
                print('test')
                # Display
                text = 'Select Sequence'
                text_area = label.Label(
                    terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
                )
                display.show(text_area)

                ### Add two lines of display, second line is sequence select
                dummy_menu_state = 0 # Modify to index based on selected
                sequencer.active_sequences[dummy_menu_state].show_sequence()

                ### Code to edit a sequence here
                key_event = keys.events.get()
                if key_event and key_event.pressed:
                    key = key_event.key_number
                    machine.last_enc1_pos = sequence_selector(
                        sequencer.active_sequences[dummy_menu_state].sequence,
                        0,
                        1,
                        0.05,
                        key,
                        machine.last_enc1_pos,
                    )
                    sequencer.active_sequences[dummy_menu_state].show_sequence()
                    neopixels.show()

                ### Update to play/pause button for final hardware
                enc_buttons_event = enc_buttons.events.get()
                if enc_buttons_event and enc_buttons_event.pressed:
                    editing_sequence = False
                ### Press encoder to exit
                ### Press play to start

        if selection is 'play_sequence':
            sequencer.play_music = True
                # Menu structure
                # Add sequence -> select file -> sequencer.add_sequence(file_sequence())
                # Edit sequence -> select existing sequence -> sequence selector


            # Play mode
            while sequencer.play_music == True:
                sequencer.play_sequence()


class MIDIState(State):
    @property
    def name(self):
        return "midi_controller"

    def enter(self, machine):
        text = "MIDI Controller"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)
        neopixels.fill((255, 0, 0))
        neopixels.show()
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def update(self, machine):
        key_event = keys.events.get()
        if key_event:
            if key_event.pressed:
                key = key_event.key_number
                send_note_on(key, 4)
                neopixels[key] = (0, 0, 255)
            if key_event.released:
                key = key_event.key_number
                send_note_off(key, 4)
                neopixels[key] = (255, 0, 0)

        neopixels.show()
        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state("menu")

class FlashyState(State):
    rainbow = False

    menu_items = [
        {
            "function": "rainbow_chase",
            "pretty": "Rainbow Chase",
        },
        {
            "function": "rainbow",
            "pretty": "Rainbow",
        },
    ]

    @property
    def name(self):
        return "flashy"

    def enter(self, machine):
        self.last_position = -4096
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        neopixels.show()
        encoder_1.position = 0
        State.exit(self, machine)

    def update(self, machine):
        position = encoder_1.position
        if position != self.last_position:
            index = position % len(
                self.menu_items
            )  # Generate a valid index from the position
            pretty_name = self.menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            text_area = label.Label(
                terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15
            )
            display.show(text_area)
            self.last_position = position
            if self.menu_items[index]["function"] == "rainbow":
                self.rainbow = Rainbow(neopixels, speed=0.1)
            elif self.menu_items[index]["function"] == "rainbow_chase":
                self.rainbow = RainbowChase(neopixels, speed=0.1)
        else:
            # All animations need to impliment animate() as their step function
            if self.rainbow and self.rainbow.animate:
                self.rainbow.animate()

        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            machine.go_to_state("menu")

class HIDState(State):
    kbd = Keyboard(usb_hid.devices)
    consumer_control = ConsumerControl(usb_hid.devices)

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

    @property
    def name(self):
        return "hid"

    def enter(self, machine):
        text = "HID Controller"
        text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=2, y=15)
        display.show(text_area)
        neopixels.fill((100, 100, 100))
        neopixels.show()
        encoder_1.position = 0
        self.last_position = 0
        State.enter(self, machine)

    def exit(self, machine):
        encoder_1.position = 0
        State.exit(self, machine)

    def update(self, machine):
        cur_position = encoder_1.position
        if cur_position != self.last_position:
            if cur_position > self.last_position:
                print("Encoder increased")
                self.consumer_control.send(ConsumerControlCode.VOLUME_INCREMENT)
            else:
                print("Encoder decreased")
                self.consumer_control.send(ConsumerControlCode.VOLUME_DECREMENT)
            self.last_position = cur_position
        #
        # Handle keyswitches
        #
        key_event = keys.events.get()
        if key_event:
            if key_event.pressed:
                print("Key pressed:", key_event.key_number)
                self.kbd.press(self.keymap[key_event.key_number])
                neopixels[key_event.key_number] = (255, 0, 0)
            if key_event.released:
                print("Key released:", key_event.key_number)
                self.kbd.release(self.keymap[key_event.key_number])
                neopixels[key_event.key_number] = (100, 100, 100)
            neopixels.show()

        enc_buttons_event = enc_buttons.events.get()
        if enc_buttons_event and enc_buttons_event.pressed:
            neopixels.fill((255, 0, 0))
            neopixels.show()
            machine.go_to_state("menu")

machine = StateMachine()
machine.add_state(StartupState())
machine.add_state(MenuState())
machine.add_state(SequencerState())
machine.add_state(SamplerState())
machine.add_state(MIDIState())
machine.add_state(FlashyState())
machine.add_state(HIDState())
sequencer = run_sequencer()

machine.go_to_state("menu")

while True:
    machine.update()
