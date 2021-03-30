#!/usr/bin/env python3
"""
    soundpad (c) 2021 Florian Streibelt <pypi@streibelt.net>

    This software is published under MIT License.
    see LICENCE for details.

    See README in the toplevel directory for more information.

    This tool enables a novation launchpad mini to be used as soundpad.

"""

import glob
import os
import sys

import pygame
from pygame import time


def launchpadpy():
        print("Currently (2021-03-11) launchpad_py has a bug preventing the top row")
        print("of LEDs to be correctly used, they will become yellow and stay on.")
        print("A fixed version can be found here: https://github.com/mutax/launchpad.py")
        print("A pull request was created at the original location.")


try:
    import launchpad_py as launchpad
except ImportError:
    try:
        import launchpad
    except ImportError:
        print("You need to install launchpad_py from https://github.com/FMMT666/launchpad.py")
        launchpadpy()
        sys.exit("error loading launchpad-py")


class Button:
    """ this class holds the state of one of the (virtual) buttons - we support multiple pages"""

    def __init__(self, r=0, g=0, snd=None, fade=100, name=None):
        self.r = r
        self.g = g
        self.snd = snd
        self.fadeout = fade
        self.name = name
        self.alt = []  # list of alternate colors
        self.has_alt = False  # to quickly filter
        self.orig = None  # color when alt was activated

        self.playmode = None

    def setColor(self, r, g):
        """sets a button color, r(ed) and g(reen) are 0..3"""

        if 3 < r < 0:
            r = 0
        if g < r < 0:
            g = 0
        self.r = r
        self.g = g

    def do_alt(self):
        """ triggered externally to cycle through all alternative colors"""

        if not self.has_alt:
            return

        if self.alt and len(self.alt) > 0:
            self.alt.insert(0, (self.r, self.g))
            self.r, self.g = self.alt.pop()

    def add_alt(self, r, g):
        """add an alternate color"""

        if not self.has_alt:
            self.orig = (self.r, self.g)

        self.alt.append((r, g))
        self.has_alt = True

    def stop_alt(self):
        """remove all alternate colors"""

        self.alt = []
        self.has_alt = False
        if self.orig:
            self.r, self.f = self.orig
            self.orig = None


class Soundboard:
    pm_zero = 0
    pm_one = 1
    pm_two = 2
    pm_three = 3

    def __init__(self):
        lp = launchpad.Launchpad()
        # we only support the Launchpad Mini!
        if not lp.Open():
            sys.exit("Did not find Launchpad Mini/Mk1 - is it connected?")

        lp.Reset()  # turn all LEDs off
        lp.ButtonFlush()  # clear events

        self.lp = lp
        self.dirty = True  # needs a redraw
        self.page = 0  # currently at the first page
        self.pages = 1  # how many pages exist
        self.maxpages = 8  # maximum pages to allow (8 buttons)
        self.state = dict()
        self.currently_pressed = set()  # to allow 'multitouch'
        self.playmode = Soundboard.pm_two
        self.channels = dict()  # save pygame audio channels in use
        self.buttons = set()  # quickly access all buttons using as set

        pygame.init()
        SONG_END = pygame.USEREVENT + 1  # custom event

    def load(self, directory):
        """ load files and add to buttons, position depends on filename"""
        print("loading files ...")
        files = []
        for extension in ('ogg', 'wav'):
            pattern = f"{directory}/*.{extension}"
            files += glob.glob(pattern)

        pos = 0
        statepos = self.translate_n(pos)
        button = self.state.get(statepos)

        for file in sorted(files):
            while button is not None:
                pos += 1
                if pos > self.maxpages * 64:
                    print(f"reached maximum pages: {self.maxpages}")
                    return
                self.pages = max(self.pages, 1 + (pos // 64))
                statepos = self.translate_n(pos)
                button = self.state.get(statepos)
            if button is None:
                snd = pygame.mixer.Sound(file)
                name = os.path.basename(file)
                button = Button(r=0, g=1, snd=snd, name=name)
                self.buttons.add(button)
                self.state[statepos] = button

    def translate_n(self, pos):
        """ translate a number n to a position in the state dict """
        x = pos % 8
        y = pos // 8
        return (x, y)

    def translateXY(self, x, y, page=None):
        """translate the physical button location to a virtual one"""
        if page is None:
            page = self.page

        offset_x = 0
        offset_y = 0 + (page * 8) - 1

        return (x + offset_x, y + offset_y)

    def draw_page(self):
        """set all LEDs according to button states"""

        if not self.dirty:  # is a redraw neccessary?
            return

        self.dirty = False  # redraw has happened

        # set page button colors (top row):
        for i in range(self.pages):
            if (i == self.page):
                self.lp.LedCtrlXY(i, 0, 3, 0)
            else:
                self.lp.LedCtrlXY(i, 0, 0, 1)

        # set play mode indicator Button "A9"
        if self.playmode == Soundboard.pm_zero:
            self.lp.LedCtrlXY(8, 1, 2, 2)  # led yellow
        elif self.playmode == Soundboard.pm_one:
            self.lp.LedCtrlXY(8, 1, 2, 0)  # led red
        elif self.playmode == Soundboard.pm_two:
            self.lp.LedCtrlXY(8, 1, 0, 2)  # led green
        else:
            self.lp.LedCtrlXY(8, 1, 0, 0)  # led off

        # set 8x8 matrix keys LEDs using rapid mode
        button_states = []  # state of all buttons in special order
        for y in range(1, 9):
            for x in range(0, 8):
                button = self.state.get(self.translateXY(x, y))  # slow but make it work, first, then optimize
                if button is None:
                    button_states.append(0)
                else:
                    button_states.append((button.g << 4) + button.r)

        self.lp.LedCtrlRawRapidHome()
        self.lp.LedCtrlRawRapid(button_states)

    def run(self):

        # some hardware might need setup
        # pygame.mixer.pre_init(channels=2, frequency=48000, allowedchanges=pygame.AUDIO_ALLOW_CHANNELS_CHANGE)
        # pygame.mixer.pre_init(channels=2, allowedchanges=pygame.AUDIO_ALLOW_CHANNELS_CHANGE)

        print("Press Buttons 1-8 to select a page")
        print("Press A9 to toggle play mode")
        print("Press B9 to stop all sounds")
        print("Hold H9 while pressing a sound button to loop that sound")
        print("Press 1 + 8 simultaneously to quit and turn off all LEDs.")
        print()
        print("Play modes:")
        print("  A9 off: stop all sounds when starting a new one (solo)")
        print("  A9 red: sound plays while button is hold down")
        print("  A9 orange: same sound plays each time a button is pressed (in parallel)")
        print("  A9 green: sounds will stop automatically")
        print()
        print("example: activate solo playmode, hold H9 and start plaing a loop")
        print("         if you now start another sound, the loop will stop")
        print("         useful for a gameshow effect.")
        print()
        print("If the toprow of LED is constantly yellow, please note:")
        launchpadpy()
        print()

        # light button B9 - a press stopps all sounds
        self.lp.LedCtrlXY(8, 2, 2, 0)  # light "stop all in B9" button
        self.lp.LedCtrlXY(8, 8, 1, 1)  # light "loop modifier in H9" button

        SONG_END = pygame.USEREVENT + 1

        # add event to all channels:
        for chanid in range(0, pygame.mixer.get_num_channels()):
            pygame.mixer.Channel(chanid).set_endevent(SONG_END)

        t = 0

        run = True
        while run:

            self.draw_page()

            time.wait(1)  # launchpad_py uses polling :(

            t = (t + 1) % 1000
            if t == 0:  # enable blinking of buttons
                for button in self.buttons:
                    if button.has_alt:
                        button.do_alt()
                        self.dirty = True

            for event in pygame.event.get():
                if event.type == SONG_END:
                    # we know one channel/file has ended, now
                    # look which one
                    delme = []
                    playing = set()  # find playing/free channels
                    for chan, button in self.channels.items():
                        if not chan.get_busy():
                            # that one has endet!
                            delme.append((chan, button))
                        else:
                            # still playing...
                            playing.add(button)

                    for chan, button in delme:
                        del (self.channels[chan])
                        if not button in playing:
                            # turn button green (sound loaded, not playing)
                            button.stop_alt()
                            button.r = 0
                            button.g = 2
                            self.dirty = True  # request redraw

            e = self.lp.ButtonStateXY()
            if e:
                if not self.handle_button(e):
                    # stop condition found
                    run = False

        self.lp.Reset()
        self.lp.Close()

    def toggle_playmode(self):
        # action on button press: toggle the playmode
        self.playmode = (self.playmode + 1) % 4
        # print(f"playmode: {self.playmode}")
        self.dirty = True

    def stop_all(self, quick=False):
        # action on button press. stopp all
        # make button yellow
        self.lp.LedCtrlXY(8, 2, 2, 2)  # stop all in B9
        # print("stopping all")

        delme = []
        for chan, button in self.channels.items():

            # fade out or stop quickly:
            if quick:
                chan.stop()
            else:
                chan.fadeout(button.fadeout or 100)
            delme.append(chan)
            button.stop_alt()
            button.r = 1
            button.g = 1
            self.dirty = True
        for chan in delme:
            del (self.channels[chan])

        # reset button
        self.lp.LedCtrlXY(8, 2, 2, 0)  # atop all in B9
        pass

    def handle_button(self, e):
        # a button was pressed

        if not e:
            return False

        bx, by, pressed = e

        if pressed:
            # add physical location to multitouch
            self.currently_pressed.add((bx, by))

            if by == 0:  # upper row, special buttons
                if bx < self.pages:
                    if bx != self.page:
                        # new page
                        self.page = bx
                        self.dirty = True

            elif bx == 8:  # right row, special purpose

                if by == 1:
                    self.toggle_playmode()
                elif by == 2:
                    self.stop_all()

            else:  # matrix keys, get status and act accordingly

                coord = self.translateXY(bx, by)
                button = self.state.get(coord)
                if button:
                    snd = button.snd
                    if snd:
                        loops = 0  # no looping
                        if (8, 8) in self.currently_pressed:
                            loops = -1

                        if self.playmode in (Soundboard.pm_zero, Soundboard.pm_one):
                            chan = pygame.mixer.Sound.play(snd, loops=loops)
                            if chan:
                                button.r = 3
                                button.g = 3
                                self.channels[chan] = button
                                if loops != 0:
                                    button.add_alt(3, 0)
                                if button.name:
                                    print(f"playing {button.name}")
                        else:
                            busy = False
                            for chan, busy_button in self.channels.items():
                                if busy_button == button and chan.get_busy():
                                    busy = True  # this sound is playing
                                    break
                            if busy:  # in this mode we want to stop it
                                pygame.mixer.Sound.fadeout(snd, button.fadeout)
                            else:  # not playing? start it!

                                stopp = set()
                                if self.playmode == Soundboard.pm_three:
                                    for chan, btn in self.channels.items():
                                        stopp.add(chan)
                                        btn.stop_alt()
                                        btn.r = 1
                                        btn.g = 1
                                        print(f"about to stop {btn.name}")

                                chan = pygame.mixer.Sound.play(snd, loops=loops)
                                if chan:
                                    button.r = 3
                                    button.g = 0
                                    self.channels[chan] = button
                                    if button.name:
                                        print(f"playing {button.name}")
                                    if loops != 0:
                                        button.add_alt(1, 0)

                                if stopp:
                                    # waiting to allow short overlap / loading of file
                                    time.wait(200)
                                    print("stopping")
                                    for chan in stopp:
                                        chan.fadeout(100)
                                        del (self.channels[chan])

                    else:
                        print("BUG: no sound???")

                self.state[coord] = button
                self.dirty = True


        else:
            self.currently_pressed.remove((bx, by))

            if by == 0:  # upper row, special buttons
                pass
            elif bx == 8:  # right row, special purpose
                pass
            else:  # matrix keys, get status and act accordingly

                coord = self.translateXY(bx, by)
                button = self.state.get(coord)
                if button:
                    if button.snd:
                        if self.playmode == Soundboard.pm_one:
                            pygame.mixer.Sound.fadeout(button.snd, button.fadeout)

        # print(self.currently_pressed)

        # multitouch to exit "H"+"1":
        if (7, 0) in self.currently_pressed and (0, 0) in self.currently_pressed:
            return False

        return True


def main():
    if len(sys.argv)==1:
        print()
        print(f"usage: {os.path.basename(sys.argv[0])} dir [dir] ...")
        print("where each dir may contain wav or ogg files")
        print("mono files with all the same sampling rate work best")
        sys.exit(0)

    board = Soundboard()

    for arg in sys.argv[1:]:
        board.load(arg)

    board.run()
    print("quitting")

if __name__ == '__main__':
    main()
