# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses
import textwrap

from ..modalpanel import ModalPanel

class Toast(ModalPanel):

    __BORDER_ROWS = 1
    __BORDER_COLS = 2
    __OUTER_GAP_ROWS = 1
    __OUTER_GAP_COLS = 1

    def __init__(self, stdscr, colors):
        super().__init__(stdscr, colors)

    def _run(self, text_lines):
        self._win.bkgd(self._colors.attr('toast'))
        for y_offset,line in enumerate(text_lines):
            self._win.addstr(self.__BORDER_ROWS + y_offset,
                             self.__BORDER_COLS,
                             line,
                             self._colors.attr('toast'))
        self._win.refresh()
        curses.napms(2000)
        curses.flushinp() # drop any keystrokes made by player during toast's delay

    def run(self, text, *args, **kwargs):
        scr_height, scr_width = self._stdscr.getmaxyx()
        toast_start_y = scr_height//10
        text_lines = textwrap.wrap(text,
                                   width=(  scr_width
                                          - 2*self.__OUTER_GAP_COLS
                                          - 2*self.__BORDER_COLS),
                                   max_lines=(  scr_height
                                              - toast_start_y
                                              - self.__OUTER_GAP_ROWS
                                              - 2*self.__BORDER_ROWS))
        max_line_width = max(len(line) for line in text_lines)
        toast_height   = len(text_lines) + 2*self.__BORDER_ROWS
        toast_width    = max_line_width  + 2*self.__BORDER_COLS
        toast_start_x  = (scr_width - toast_width)//2
        super().run(toast_height,
                    toast_width,
                    toast_start_y,
                    toast_start_x,
                    (line.center(max_line_width) for line in text_lines),
                    *args,
                    **kwargs)
