from StartupState import StartupState
from FlashyState import FlashyState
from MIDIState import MIDIState
from HIDState import HIDState
from MenuState import MenuState
from SequencerState import SamplerMenuState, SequencerMenuState, SequencerPlayState


class StateMachine(object):
    def __init__(self):
        self.state = None
        self.states = {}
        self.animation = None
        self.last_state = None

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if self.state:
            self.state.exit(self)
            self.last_state = self.state.name
        self.state = self.states[state_name]
        self.state.enter(self)

    def update(self):
        if self.state:
            self.state.update(self)


machine = StateMachine()
machine.add_state(StartupState())
machine.add_state(FlashyState())
machine.add_state(MIDIState())
machine.add_state(HIDState())
machine.add_state(MenuState())
machine.add_state(SamplerMenuState())
machine.add_state(SequencerMenuState())
machine.add_state(SequencerPlayState())
machine.go_to_state("startup")

while True:
    machine.update()
