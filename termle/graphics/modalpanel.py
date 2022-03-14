# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import abc
import copy
import curses
import curses.panel

from . import paneliterator

from .input import Input

class ModalPanel(abc.ABC):

    def __init__(self, stdscr, colors):
        self._stdscr = stdscr
        self._win    = None
        self._panel  = None
        self._colors = copy.deepcopy(colors)
        self._input  = None

    @abc.abstractmethod
    def _run(self):
        pass

    def run(self, height, width, start_y, start_x, *args, **kwargs):

        # create new window, and corresponding panel
        self._win   = curses.newwin(height, width, start_y, start_x)
        self._panel = curses.panel.new_panel(self._win)
        curses.panel.update_panels()
        curses.doupdate()

        # clear window
        self._win.clear()

        # setup input
        self._input = Input(self._stdscr, self._win, self.__class__.__name__)

        # run derived panel class's logic
        self._run(*args, **kwargs)

        # "close" window and restore previous window
        self._panel.hide() # hides _panel (and its window) and removes it from panel stack
        curses.panel.update_panels()
        curses.doupdate()
        for panel in paneliterator.back_to_front():
            panel.window().redrawwin()
