import time

from setup import (
    select_enc,
    volume_enc,
)

from StartupState import StartupState


class StateMachine(object):
    def __init__(self):
        self.state = None
        self.states = {}
        self.last_select_pos = select_enc.position
        self.last_volume_pos = volume_enc.position
        self.paused_state = None
        self.ticks_ms = 0
        self.animation = None

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
            if self.ticks_ms > 0:
                time.sleep(self.ticks_ms / 1000)

    # When pausing, don't exit the state
    def pause(self):
        self.state = self.states["paused"]
        self.state.enter(self)

    # When resuming, don't re-enter the state
    def resume_state(self, state_name):
        if self.state:
            self.state.exit(self)
        self.state = self.states[state_name]


machine = StateMachine()
machine.add_state(StartupState())
machine.go_to_state("startup")

while True:
    machine.update()
