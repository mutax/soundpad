# soundpad

A small utility that allows using a novation launchpad mini to be used as soundboard
in Linux. Initially planned as proof of concept, people asked me for the code, so
here it is.

# Purpose

Play funny sounds during boring meetings during covid.

# Usage

Invoke it with a list of directories that contain wav and ogg files. They will be
loaaded dir after dir and mapped to the buttons.

The files can be played in various modes of operation.

## Special buttons

Press Buttons 1-8 to select a page

Press A9 to toggle play mode

Press B9 to stop all sounds

Hold H9 while pressing a sound button to loop that sound

Press 1 + 8 simultaneously to quit and turn off all LEDs.


## Play modes:

A9 off: stop all sounds when starting a new one (solo)")

A9 red: sound plays while button is hold down")

A9 orange: same sound plays each time a button is pressed (in parallel)")

A9 green: sounds will stop automatically")


## Example

activate solo playmode, hold down H9 and press a button to start plaing a loop,
if you now start another sound, the loop will stop and the new file play once.
Useful for a gameshow effect



# Platform

Tested with debian GNU/Linux.

# Requirements

A novation launchpad mini - others may work too, but I removed the configuration
as this utility was planned as a proof of concept only.

Also pygame and the lauchpad\_py.

You can find launchpad\_py athttps://github.com/FMMT666/launchpad.py

Note that currently (2021-03-11) the version has a bug preventing the top row
of leds to be correctly used, they will become yellow and stay on.

A fixed version can be found here: https://github.com/mutax/launchpad.py until
the pull request with the fix is merged.






