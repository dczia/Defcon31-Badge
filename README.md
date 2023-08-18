# Defcon31-Badge
DCZia 2023 DC31 Badge - Electric Sampler

```
   ____  ___________   _          ________          __       _
   / __ \/ ____/__  /  (_)___ _   / ____/ /__  _____/ /______(_)____
  / / / / /      / /  / / __ `/  / __/ / / _ \/ ___/ __/ ___/ / ___/
 / /_/ / /___   / /__/ / /_/ /  / /___/ /  __/ /__/ /_/ /  / / /__
/_____/\____/  /____/_/\__,_/  /_____/_/\___/\___/\__/_/  /_/\___/

   _____                       __
  / ___/____ _____ ___  ____  / /__  _____
  \__ \/ __ `/ __ `__ \/ __ \/ / _ \/ ___/
 ___/ / /_/ / / / / / / /_/ / /  __/ /
/____/\__,_/_/ /_/ /_/ .___/_/\___/_/
                    /_/
```


## About
The DCZia Electric Sampler - A eurorack format drum machine, sampler, and step sequencer powered by
the Pi2040.

## Specs

RPI 2040 Microconroller
OLED Screen
3.5mm Audio Out Jack
3.5mm Midi In / Out (TRRS)
3.5mm Sync In / Out
MicroSD Card Slot
Eurorack Power Connector
Battery Power


## Build Guide

The badge comes with all surface mount components already assembled on the board. You will need to
solder on the keyswitches, audio jacks, screen, rotary encoders, and battery box.

First add the audio jacks. Install all the jacks and make sure they are flat and perpendicular with
the board. Next install the front board first aligning the jacks with the holes in the front board.
Then connect the bottom pin header to the front board. The header will be off by one, THIS IS OK for
the v1.1 board! Then carefully flip over the board and solder on the jacks.

Remove the front panel.

Then insert a keyswitch, or all keyswitches onto the board. Check that the metal pins are not bent,
and if so gently straignten them out with your fingers or a pair of tweezers. Carfully flip the
board over and solder on the keyswitches.

Next add the rotary encoders. Push them through the board, and you may need to gently fold in the
side stabilization pins if they do not line up correctly. Flip over the board and solder these in. 

Next with the board facing forward and on a flat surface, put the screen in. The legs of the screen
should not protrude through the back of the board past the holes, or only a tiny bit. You may need
to use something like a pencil or something to help the screen lay flat, standing off from the
board. Gently solder from the front to establish a mechanical connection to the board, then once the
screen is secure, flip over and solder the back. You must solder the back pads to endure a
connection from the screen to the microcrontroller. 

Finally flip the board over and gently attach the battery pack somewhere on the back with the
supplied double sticky tape. Then solder on the leads from the battery pack to the pads on the
bottom left side of the back of the board.


## User Manual

Currently the firmware is not complete, and the user interface may change.

The Select Knob will change between options on the screen, and push selects the currently
highlighted option.

The Volume knob will change the volume.

The PLAY button will play / pause any currently running program

There are a few modes on the v1 software.
A LED light mode.
A Sampler mode with a sequencer. You can load a wav file from the onboard flash, and then add a sequence and control the steps with the 8 key switches, and adjust per step volume.
A Sequencer mode which will play pre progarmed sequences. (Still under dev)
A Midi controller mode. You can adjust what notes / cc params are output via the python code in our repo.
A USB HID Device mode. The keys will output 0-9 and the device will emulate a keyboard.


## Notes

If you picked up a V1 board at Con, the board shipped with our testing firmware. Please flash the V1 firmware for more features.

Additional Features and changes will be coming soon!

## Updating the software / firmware

To update the software on the board you can do two things.

1. Use the fimware blob from our release section. To use this, unplug and turn off the module. Using something non conductivem press and hold the button on the RPI 2040 (The BootSelect Button) while powering on the unit via a micro usb cable. You should then see a mass storage drive appear on your computer. Drag the single uf2 file onto the drive. Then the unit should restart with the new firmware.

2. You can also plug the unit into your computer via the micro usb and drag the contents of the Production/Software folder onto the mass storage drive. The unit should reboot when complete. Sometimes if your computer transfers the files too slow this can cause issues with the RPI rebooting before all the software is complete.
