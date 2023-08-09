import audiobusio
import audiomixer
import board
import terminalio
import time

from adafruit_display_text import label
from adafruit_led_animation.animation.rainbow import Rainbow
from audiocore import WaveFile
from MIDIState import send_note_on, send_note_off
from os import listdir
from supervisor import ticks_ms

from State import State
from utils import (
    selector_calcs,
    show_menu,
    neoindex,
)
from setup import (
    display,
    keys,
    neopixels,
    select_enc,
    volume_enc,
)


class file_sequences:
    files = []
    sequences = []
    # File sequencer class
    # Sets up a sequence track to play a .wav file sample at regular intervals
    # 8 step sequence tells whether to play

    def add_sequence(self, fname):
        self.files.append(fname)
        self.sequences.append(
            [
                [True, 0.5],
                [True, 0.5],
                [True, 0.5],
                [True, 0.5],
                [True, 0.5],
                [True, 0.5],
                [True, 0.5],
                [True, 0.5],
            ]
        )

    def show_sequence(self, sequence_index):
        for index, item in enumerate(self.sequences[sequence_index]):
            if item[0]:
                mapped_neopixel = neoindex(index)
                neopixels[mapped_neopixel] = (0, 0, 255)
                neopixels.show()
            elif item[0] is False:
                mapped_neopixel = neoindex(index)
                neopixels[mapped_neopixel] = (255, 0, 0)
                neopixels.show()


# MIDI sequencer class
# Sets up a sequence track to play MIDI messages at regular intervals
class midi_sequences:
    sequences = []

    def add_sequence(self):
        # Format [play, note, octave]
        self.sequences.append(
            [
                [True, 1, 2],
                [True, 3, 2],
                [True, 1, 2],
                [True, 5, 2],
                [True, 1, 2],
                [True, 3, 2],
                [True, 5, 2],
                [True, 3, 2],
            ]
        )

    def show_sequence(self):
        for index, item in enumerate(self.sequence):
            if item[0]:
                mapped_neopixel = neoindex(index)
                neopixels[mapped_neopixel] = (0, 0, 255)
                neopixels.show()
            elif item[0] is False:
                mapped_neopixel = neoindex(index)
                neopixels[mapped_neopixel] = (255, 0, 0)
                neopixels.show()


class SequencerMenuState:
    sequencer_mode = "midi"

    @property
    def name(self):
        return "sequencer_menu"

    def enter(self, machine):
        neopixels.fill((0, 0, 0))
        text = "MIDI Sequencer Menu"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=10)
        display.show(text_area)
        keys.events.clear()
        State.enter(self, machine)

    def play_midi(self):
        pass

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        self.color = (0, 0, 0)
        State.exit(self, machine)

    def update(self, machine):
        key_event = keys.events.get()
        if key_event and key_event.pressed:
            if key_event.key_number == 8:
                machine.go_to_state("sequencer_play")
            if key_event.key_number == 10:
                machine.go_to_state("menu")


class SamplerMenuState(State):
    sequencer_mode = "sampler"
    menu_items = [
        {
            "name": "add_sequence",
            "pretty": "Add Sequence",
        },
        {
            "name": "remove_sequence",
            "pretty": "Remove Sequence",
        },
        {
            "name": "edit_sequence",
            "pretty": "Edit Sequence",
        },
        {
            "name": "play_sequence",
            "pretty": "Play Sequence",
        },
        {
            "name": "exit",
            "pretty": "Exit",
        },
    ]

    @property
    def name(self):
        return "sampler_menu"

    def __init__(self):
        self.total_lines = 3
        self.list_length = len(self.menu_items)
        self.highlight = 1
        self.shift = 0
        # Get list of samples ONCE
        wav_files = []
        files = listdir("/samples/")
        for file in files:
            if file.endswith(".wav") and (not file.startswith(".")):
                wav_files.append({"name": file, "pretty": file})
        self.samples = wav_files

    def enter(self, machine):
        self.highlight = 1
        self.shift = 0
        self.last_position = 0
        if machine.animation is None:
            machine.animation = Rainbow(neopixels, speed=0.1)
        show_menu(self.menu_items, self.highlight, self.shift)
        State.enter(self, machine)

    def exit(self, machine):
        State.exit(self, machine)

    def select_wav(self):
        # Reset menu status
        self.highlight = 1
        self.shift = 0
        # Show valid files, select with encoder knob/button
        while True:
            if self.last_position != select_enc.position:
                (self.highlight, self.shift) = selector_calcs(
                    self.samples,
                    self.highlight,
                    self.shift,
                    self.last_position,
                    select_enc.position,
                )
                self.last_position = select_enc.position
            show_menu(self.samples, self.highlight, self.shift)
            key_event = keys.events.get()
            if key_event and key_event.pressed:
                selection = self.samples[self.highlight - 1 + self.shift]["name"]
                # Reset menu status
                self.highlight = 1
                self.shift = 0
                return selection

    def select_sequence(self, sequence_array):
        # Reset menu status
        self.highlight = 1
        self.shift = 0
        # Show valid sequences, select with encoder knob/button
        seq_select = []
        for index, seq in enumerate(sequence_array):
            seq_select.append({"name": f"{index}", "pretty": f"{index}: {seq}"})

        while True:
            if self.last_position != select_enc.position:
                (self.highlight, self.shift) = selector_calcs(
                    seq_select,
                    self.highlight,
                    self.shift,
                    self.last_position,
                    select_enc.position,
                )
                self.last_position = select_enc.position
            show_menu(seq_select, self.highlight, self.shift)
            key_event = keys.events.get()
            if key_event and key_event.pressed:

                selection = self.highlight - 1 + self.shift
                return selection

    # Function to program sequence values, should be used after a keypress
    # On key release toggle state
    # On key held and encoder turned, value changed
    def sequence_selector(self, value, min_val, max_val, increment, key_val):
        selection = True
        vel_change = False
        select_position = select_enc.position
        # Display current value
        while selection:
            text = f"Step {key_val}: {value[key_val][1]:.2f}"
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=5)
            display.show(text_area)
            key_event = keys.events.get()

            # Modify value on encoder input
            if select_position is not select_enc.position:
                if select_enc.position < select_position:
                    if value[key_val][1] > min_val + increment:
                        value[key_val][1] = value[key_val][1] - increment
                    else:
                        value[key_val][1] = min_val

                else:
                    if value[key_val][1] < max_val - increment:
                        value[key_val][1] = value[key_val][1] + increment
                    else:
                        value[key_val][1] = max_val
                select_position = select_enc.position
                vel_change = True

            # Exit selection menu if key released
            if key_event and key_event.released:
                if key_event.key_number == key_val:
                    if not vel_change:
                        value[key_val][0] = not value[key_val][0]
                    selection = False

    def add_sequence(self, fsequences):
        wav_file = self.select_wav()
        file_sequences.files.append(wav_file)
        file_sequences.add_sequence()

    def edit_sequence(self, fsequences):
        # Check if sequences exist
        if len(file_sequences.files) == 0:
            text = "No Active Sequences"
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
            display.show(text_area)
            time.sleep(0.5)
        else:
            editing_sequence = True

            # Select sequence
            selected_sequence = self.select_sequence(
                file_sequences.files
            )  # Modify to index based on selected

            # Display
            text = f"Edit {file_sequences.files[selected_sequence]}"
            text_area = label.Label(terminalio.FONT, text=text, x=2, y=15)
            display.show(text_area)

            file_sequences.show_sequence(selected_sequence)
            neopixels.show()

            while editing_sequence is True:
                # Code to edit a sequence here
                key_event = keys.events.get()
                if key_event and key_event.pressed:
                    key = key_event.key_number
                    if key >= 0 and key <= 7:
                        self.sequence_selector(
                            file_sequences.sequences[selected_sequence],
                            0,
                            1,
                            0.05,
                            key,
                        )
                        file_sequences.show_sequence(selected_sequence)
                        neopixels.show()

                # Exit on click of select encoder
                key_event = keys.events.get()
                if key_event and key_event.pressed and key_event.key_number == 10:
                    # Reset menu status
                    self.highlight = 1
                    self.shift = 0
                    # Exit editing menu
                    editing_sequence = False


    def remove_sequence(self, fsequences):
        pass

    def update(self, machine):
        selection = ""
        # Code for moving through menu and selecting mode
        if machine.animation:
            machine.animation.animate()
        # Some code here to use an encoder to scroll through menu options, press to select one
        position = select_enc.position

        if self.last_position != position:
            if position < self.last_position:
                if self.highlight > 1:
                    self.highlight -= 1
                else:
                    if self.shift > 0:
                        self.shift -= 1
            else:
                if self.highlight < self.total_lines:
                    self.highlight += 1
                else:
                    if self.shift + self.total_lines < self.list_length:
                        self.shift += 1
            show_menu(self.menu_items, self.highlight, self.shift)
        self.last_position = position

        key = keys.events.get()
        if key and key.pressed:
            selection = self.menu_items[self.highlight - 1 + self.shift]["name"]
        if selection == "play_sequence":
            machine.go_to_state("sequencer_play")
        if selection == "add_sequence":
            wav_file = self.select_wav()
            file_sequences.add_sequence(wav_file)
            show_menu(self.menu_items, self.highlight, self.shift)
        if selection == "edit_sequence":
            self.edit_sequence(file_sequences)
            show_menu(self.menu_items, self.highlight, self.shift)
        if selection == "exit":
            machine.go_to_state("menu")


class SequencerPlayState(State):
    clk_src = "int"
    color = (0, 0, 0)
    volume = 0.2
    step = 0
    sequencer_mode = "sampler"
    sampler_files = []
    sampler_voices = []
    bpm = 300

    @property
    def name(self):
        return "sequencer_play"

    def enter(self, machine):
        # Clear key states
        keys.events.clear()
        # Get current encoder positions
        self.volume_position = volume_enc.position
        self.select_position = select_enc.position

        # Display menu text
        text = "Playing"
        text_area = label.Label(terminalio.FONT, text=text, x=2, y=10)
        display.show(text_area)

        # Midi sequence setup
        if machine.last_state == "sequencer_menu":
            self.sequencer_mode = "midi"

        # Sampler sequence setup
        elif machine.last_state == "sampler_menu":
            self.sequencer_mode = "sampler"
            # Setup audio
            self.audio = audiobusio.I2SOut(board.GP0, board.GP1, board.GP2)
            num_voices = 10
            self.mixer = audiomixer.Mixer(
                voice_count=num_voices,
                sample_rate=22050,
                channel_count=1,
                bits_per_sample=16,
                samples_signed=True,
            )

            # Load files
            for item in file_sequences.files:
                self.sampler_files.append(open(f"/samples/{item}", "rb"))
                self.sampler_voices.append(WaveFile(self.sampler_files[-1]))

            # Delay to avoid audio click
            time.sleep(0.1)
            self.audio.play(self.mixer)
        State.enter(self, machine)

    def exit(self, machine):
        neopixels.fill((255, 0, 0))
        self.color = (0, 0, 0)
        State.exit(self, machine)

    def timed_midi(self):
        current_midi = midi_sequences.sequences[0][self.step]
        if current_midi[0] is True:
            send_note_on(current_midi[1], current_midi[2])
        step_start = ticks_ms()
        while ticks_ms() < step_start + self.step_length:
            pass
        if current_midi[0] is True:
            send_note_off(current_midi[1], current_midi[1])

    def play_voices(self):
        for index, item in enumerate(self.sampler_voices):
            self.mixer.voice[index].level = self.volume  # * sample volume
            self.mixer.voice[index].play(item)

    def stop_voices(self):
        for index, item in enumerate(self.sampler_voices):
            self.mixer.voice[index].stop()

    def timed_sampler(self):
        # Play
        for index, sequence in enumerate(file_sequences.sequences):
            if sequence[self.step][0] is True:
                self.mixer.voice[index].level = self.volume * sequence[self.step][1]
                self.mixer.voice[index].play(self.sampler_voices[index])
        step_start = ticks_ms()
        while ticks_ms() < (step_start + self.step_length):
            pass
        # I don't think we need to kill voices, but leaving this here just in case
        # self.stop_voices()

    def adjust_bpm(self):
        # Adjust bpm if select_enc state changes
        if self.select_position is not select_enc.position:
            diff = abs(select_enc.position - self.select_position)
            if select_enc.position < self.select_position:
                if self.bpm >= (20 + diff):
                    self.bpm = int(self.bpm - diff)
                else:
                    self.bpm = 20
            if select_enc.position > self.select_position:
                if self.bpm <= (300 - diff):
                    self.bpm = int(self.bpm + diff)
                else:
                    self.bpm = 300
            select_enc.position = self.select_position
            # Display text would be nice, but this makes the audio chirp *shrug*
            # text = f"BPM: {self.bpm}"
            # text_area = label.Label(terminalio.FONT, text=text, x=2, y=10)
            # display.show(text_area)

    def adjust_volume(self):
        self.audio.stop()
        while self.audio.playing:
            pass
        # Adjust volume if volume_enc state changes
        if self.volume_position is not volume_enc.position:
            if volume_enc.position < self.volume_position:
                if self.volume >= 0.05:
                    self.volume = self.volume - 0.05
                else:
                    self.volume = 0
            if volume_enc.position > self.volume_position:
                if self.volume <= 0.95:
                    self.volume = self.volume + 0.05
                else:
                    self.volume = 1
            volume_enc.position = self.volume_position
            # Display text would be nice, but this makes the audio chirp *shrug*
            # text = f"Volume: {self.volume}"
            # text_area = label.Label(terminalio.FONT, text=text, x=2, y=10)
            # display.show(text_area)
        self.audio.play(self.mixer)

    def key_check(self, state_machine):
        key_event = keys.events.get()
        if key_event and key_event.pressed:
            # Return to sequencer menu if select pressed
            if key_event.key_number == 10:
                try:
                    self.audio.deinit()
                except:
                    pass
                keys.events.clear()
                if self.sequencer_mode == "midi":
                    state_machine.go_to_state("sequencer_menu")
                elif self.sequencer_mode == "sampler":
                    state_machine.go_to_state("sampler_menu")
            # Pause if play/pause pressed
            if key_event.key_number == 8:
                keys.events.clear()
                self.pause_sequencer()
        keys.events.clear()

    def step_update(self):
        if self.step < 7:
            self.step += 1
        else:
            self.step = 0

    def pause_sequencer(self):
        pause_state = True
        self.stop_voices()
        # Display text would be nice, but this makes the audio chirp *shrug*
        # text = "Paused"
        # text_area = label.Label(terminalio.FONT, text=text, x=2, y=10)
        # display.show(text_area)
        while pause_state is True:
            key_event = keys.events.get()
            if key_event and key_event.pressed and key_event.key_number == 8:
                keys.events.clear()
                pause_state = False

    def update(self, machine):
        self.step_length = int(1000 // (self.bpm / 60))
        if self.sequencer_mode == "sampler":
            if self.clk_src == "int":
                self.timed_sampler()
                self.adjust_volume()
        elif self.sequencer_mode == "midi":
            if self.clk_src == "int":
                self.timed_midi()
        self.adjust_bpm()
        self.step_update()
        self.key_check(machine)


midi_sequences = midi_sequences()
midi_sequences.add_sequence()
file_sequences = file_sequences()
# file_sequences.add_sequence("/samples/Tom.wav")
# file_sequences.add_sequence('/samples/Snare.wav')
