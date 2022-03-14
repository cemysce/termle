# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses
import _curses

from collections import defaultdict

from .exceptions import WindowResized

class Input:

    def __init__(self, stdscr, this_window, this_panel_name):
        self.__stdscr                               = stdscr
        self.__this_window                          = this_window
        self.__this_panel_name                      = this_panel_name
        (self.__rows, self.__cols)                  = self.__stdscr.getmaxyx()
        self.__click_map_yx                         = defaultdict(lambda: None)
        self.__action_or_value_for_last_mouse_press = None
        self.__timeout_action_or_value              = None

        # enable ncurses to pre-process complex inputs (ex. backspace, mouse buttons)
        self.__this_window.keypad(True)

    def add_default_to_click_map(self, action_or_value):
        self.__click_map_yx.default_factory = lambda: action_or_value

    def add_to_click_map(self, y, x, height, width, action_or_value):
        for coords in ((y+g,x+i) for g in range(height) for i in range(width)):
            self.__click_map_yx[coords] = action_or_value

    def set_blocking(self):
        self.__timeout_action_or_value = None
        self.__this_window.timeout(-1)

    def set_non_blocking(self, delay_msec, timeout_action_or_value):
        if delay_msec < 0 or timeout_action_or_value is None:
            raise
        self.__timeout_action_or_value = timeout_action_or_value
        self.__this_window.timeout(delay_msec)

    def get(self, min_required_total_height, min_required_total_width):
        try:
            k = self.__this_window.getkey()
        except _curses.error as e:
            if str(e) == 'no input':
                k = None
                if callable(self.__timeout_action_or_value):
                    self.__timeout_action_or_value()
                else:
                    k = self.__timeout_action_or_value
                return k
            raise

        # handle resize
        current_rows, current_cols = self.__stdscr.getmaxyx()
        if (self.__rows, self.__cols) != (current_rows, current_cols):
            raise WindowResized(current_rows,
                                current_cols,
                                min_required_total_height,
                                min_required_total_width,
                                self.__this_panel_name)

        # handle mouse click
        if k == 'KEY_MOUSE':
            k = None
            (m_id, m_x, m_y, m_z, m_bstate) = curses.getmouse()
            (w_y, w_x) = self.__this_window.getbegyx()
            m_y -= w_y
            m_x -= w_x
            if m_bstate & curses.BUTTON1_PRESSED:
                self.__action_or_value_for_last_mouse_press = self.__click_map_yx[(m_y, m_x)]
            elif m_bstate & curses.BUTTON1_RELEASED:
                action_or_value = self.__click_map_yx[(m_y, m_x)]
                if action_or_value == self.__action_or_value_for_last_mouse_press:
                    if callable(action_or_value):
                        action_or_value()
                    else:
                        k = action_or_value

        # return key
        return k
