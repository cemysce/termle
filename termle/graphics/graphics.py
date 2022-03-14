# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses
import functools
import os
import signal
import sys

from .colors      import Colors
from .exceptions  import ColorsChanged, WindowResized
from .panels.main import MainPanel

class Graphics:

    def __init__(self, game_core, config, game_num_str=None):

        self.__game_core    = game_core
        self.__config       = config
        self.__game_num_str = game_num_str

        # values to be initialized later
        self.__stdscr = None
        self.__colors = None
        self.__rows   = None
        self.__cols   = None

    def __run(self, stdscr, jump_to_panel=None):
        self.__stdscr = stdscr

        # initialize some ncurses stuff (hide cursor, setup mouse)
        curses.curs_set(False)
        curses.mouseinterval(0)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)

        # initialize some of our own stuff (colors to use with ncurses,
        #  cache of window size to be able to detect resize later)
        self.__colors              = Colors(self.__config.dark_mode,
                                            self.__config.high_contrast_mode)
        (self.__rows, self.__cols) = self.__stdscr.getmaxyx()

        # create and run main panel window
        main_panel = MainPanel(self.__stdscr,
                               self.__colors,
                               self.__game_core,
                               self.__config,
                               self.__game_num_str)
        main_panel.run(height=0,
                       width=0,
                       start_y=0,
                       start_x=0,
                       jump_to_panel=jump_to_panel)

    def run(self):
        aborted_panel_name = None
        while True:
            try:
                curses.wrapper(functools.partial(self.__run,
                                                 jump_to_panel=aborted_panel_name))
                break
            except ColorsChanged as e:
                aborted_panel_name = e.aborted_panel_name
            except WindowResized as e:
                aborted_panel_name = e.aborted_panel_name
                if e.too_small:
                    print(f'Terminal must be at least {e.min_width} columns by'
                          f' {e.min_height} rows.',
                          file=sys.stderr)
                    while any(sz < min_sz
                              for sz,min_sz in zip(os.get_terminal_size(),
                                                   (e.min_width, e.min_height))):
                        signal.sigwaitinfo([signal.SIGWINCH])
