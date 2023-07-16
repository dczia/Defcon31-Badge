# Defcon31-Badge
DCZia 2023 DC31 Badge - Electric Sampler

```
__________________________
___  __ \_  ____/__  /__(_)_____ _
__  / / /  /    __  /__  /_  __ `/
_  /_/ // /___  _  /__  / / /_/ /
/_____/ \____/  /____/_/  \__,_/

_______________          _____       _____
___  ____/__  /____________  /__________(_)______
__  __/  __  /_  _ \  ___/  __/_  ___/_  /_  ___/
_  /___  _  / /  __/ /__ / /_ _  /   _  / / /__
/_____/  /_/  \___/\___/ \__/ /_/    /_/  \___/

________                         ______
__  ___/_____ _______ ______________  /____________
_____ \_  __ `/_  __ `__ \__  __ \_  /_  _ \_  ___/
____/ // /_/ /_  / / / / /_  /_/ /  / /  __/  /
/____/ \__,_/ /_/ /_/ /_/_  .___//_/  \___//_/
```


## About
The DCZia Electric Sampler - A eurorack format sampler and step sequencer in a badge, powered by the  Pi2040  


## Todo

[ ] Add Main Menu

[ ] Improve Input Control Flow Between States

[ ] Write Sequencer Code

    Ideally editable from device, and can be used to load sequence into sampler mode or MIDI sequencer mode

[ ] Develop Party Mode Lighting Sequences

[ ] Write Display Code

    Libraries for display and basic functional code added

[ ] Write Lighting Code

    Neopixel library added, several bits of simple code added

[ ] Write sync code

    Functional sync out code in testing branch, need to bodge sync in for testing

[X] Write MIDI code

    MIDI controller mode working well enough for minimum viable product

[ ] Expand MIDI Functionality

    Add more control of notes, add control signals, expand to include USB MIDI

[ ] Write sample playback code

    Single track sample playback code included
    Need to expand to multi-track, lots of room for further improvements

[ ] Write Button handling code

    All prototype buttons functional, minimal code for actually controlling flow complete
    Library includes matrix inputs for final product

[ ] Add Documentation Here.

[ ] ...

[ ] Profit? 


## Notes
Latest code requires screen bodge to function (cut traces to SCK and SDA, solder wires on to swap them)

Encoder button will cycle through implemented modes

MIDI Controller works. First set of protos had R4 and C3 swapped and running MIDI may cause hot and/or fire

In sequencer mode, first keyswitch will start/stop code. Press encoder button while stopped to cycle back to menu
