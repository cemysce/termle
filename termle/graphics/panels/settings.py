# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses
import _curses

import fancytext

from version import __version__

from ..           import glyphs
from ..exceptions import ColorsChanged, WindowResized
from ..modalpanel import ModalPanel

from .toast import Toast

class SettingsPanel(ModalPanel):

    def __init__(self, stdscr, colors, config, game_core, game_num_str=None):
        super().__init__(stdscr, colors)
        self.__config               = config
        self.__game_core            = game_core
        self.__game_num_str         = game_num_str
        self.__rows                 = None
        self.__cols                 = None
        self.__next_row_for_drawing = None
        self.__closing              = None

    def __draw_header(self):
        PANEL_TITLE = 'SETTINGS'
        panel_title_start_x = self.__cols//2 - len(PANEL_TITLE)//2
        self._win.addstr(self.__next_row_for_drawing,
                         panel_title_start_x,
                         PANEL_TITLE,
                         curses.A_BOLD|self._colors.attr('text_default'))
        self._win.addstr(self.__next_row_for_drawing,
                         self.__cols-1,
                         glyphs.X_BUTTON, # 🞩
                         self._colors.attr('header_button'))
        self._input.add_to_click_map(self.__next_row_for_drawing, self.__cols-1, 1, 1, self.__close)
        self.__next_row_for_drawing += 2

    def __draw_toggle(self, enabled, action, text, subtext=None, enableable=True):
        self._win.addstr(self.__next_row_for_drawing, 0, text, self._colors.attr('text_default'))
        if self.__config.dark_mode:
            if enabled:
                # ■■
                self._win.addstr(self.__next_row_for_drawing, self.__cols-2, '\u25a0', self._colors.attr('switch_on_gap'))
                self._win.addstr(self.__next_row_for_drawing, self.__cols-1, '\u25a0', self._colors.attr('switch_on'))
            else:
                # ■■
                self._win.addstr(self.__next_row_for_drawing, self.__cols-2, '\u25a0', self._colors.attr('switch_off'     if enableable else 'switch_off_insensitive'))
                self._win.addstr(self.__next_row_for_drawing, self.__cols-1, '\u25a0', self._colors.attr('switch_off_gap' if enableable else 'switch_off_gap_insensitive'))
        else:
            if enabled:
                # ■□
                self._win.addstr(self.__next_row_for_drawing, self.__cols-2, '\u25a0', self._colors.attr('switch_on_gap'))
                self._win.addstr(self.__next_row_for_drawing, self.__cols-1, '\u25a1', self._colors.attr('switch_on'))
            else:
                # □■
                self._win.addstr(self.__next_row_for_drawing, self.__cols-2, '\u25a1', self._colors.attr('switch_off'     if enableable else 'switch_off_insensitive'))
                self._win.addstr(self.__next_row_for_drawing, self.__cols-1, '\u25a0', self._colors.attr('switch_off_gap' if enableable else 'switch_off_gap_insensitive'))
        self._input.add_to_click_map(self.__next_row_for_drawing, self.__cols-2, 1, 2, action)
        self.__next_row_for_drawing += 1
        if subtext:
            self._win.addstr(self.__next_row_for_drawing,
                             0,
                             fancytext.superscript(subtext),
                             self._colors.attr('subtext'))
        self.__next_row_for_drawing += 1

    def __draw_separator(self):
        self._win.addstr(self.__next_row_for_drawing,
                         0,
                         self.__cols*glyphs.HORIZONTAL_LINE_SEGMENT,
                         self._colors.attr('separator_line'))
        self.__next_row_for_drawing += 1

    def __draw_footer(self):
        if self.__game_num_str:
            (game_num_display_str_width,
             game_num_display_str) = fancytext.subscript(f'#{self.__game_num_str}',
                                                        calc_width=True)
            self._win.addstr(self.__rows-2,
                             self.__cols-game_num_display_str_width,
                             game_num_display_str,
                             self._colors.attr('subtext'))
        self._win.addstr(self.__rows-1,
                         0,
                         fancytext.superscript('(c) 2022 cemysce'),
                         self._colors.attr('subtext'))
        (version_display_str_width,
         version_display_str) = fancytext.superscript(f'v{__version__}',
                                                      calc_width=True)
        try:
            # below addstr call will run into
            #  https://stackoverflow.com/questions/36387625, so we catch
            #  the exception and ignore it
            self._win.addstr(self.__rows-1,
                             self.__cols-version_display_str_width,
                             version_display_str,
                             self._colors.attr('subtext'))
        except _curses.error:
            pass

    def __close(self):
        self.__closing = True

    def __toggle_hard_mode(self):
        if self.__game_core.in_progress() and not self.__config.hard_mode:
            toast = Toast(self._stdscr, self._colors)
            toast.run('Hard mode can only be enabled at the start of a round')
        else:
            if not self.__game_core.toggle_hard_mode(not self.__config.hard_mode):
                raise
            self.__config.hard_mode = not self.__config.hard_mode
            next_row_for_drawing__oldval = self.__next_row_for_drawing
            self.__next_row_for_drawing = self.__row_for_hard_mode_toggle
            self.__draw_toggle(self.__config.hard_mode,
                               self.__toggle_hard_mode,
                               'Hard Mode',
                               'Hints must be used in next guess',
                               enableable=not self.__game_core.in_progress())
            self.__next_row_for_drawing = next_row_for_drawing__oldval

    def __toggle_dark_mode(self):
        self.__config.dark_mode = not self.__config.dark_mode
        raise ColorsChanged(self.__class__.__name__)

    def __toggle_high_contrast_mode(self):
        self.__config.high_contrast_mode = not self.__config.high_contrast_mode
        raise ColorsChanged(self.__class__.__name__)

    def _run(self,
             parent_min_required_total_height,
             parent_min_required_total_width):

        # set background
        self._win.bkgd(self._colors.attr('background'))

        # some init
        self.__rows, self.__cols = self._win.getmaxyx()
        self.__next_row_for_drawing = 0
        self.__closing              = False

        # draw panel
        self.__draw_header()
        self.__row_for_hard_mode_toggle = self.__next_row_for_drawing
        self.__draw_toggle(self.__config.hard_mode,          self.__toggle_hard_mode,          'Hard Mode', 'Hints must be used in next guess', enableable=not self.__game_core.in_progress())
        self.__draw_separator()
        self.__draw_toggle(self.__config.dark_mode,          self.__toggle_dark_mode,          'Dark Theme')
        self.__draw_separator()
        self.__draw_toggle(self.__config.high_contrast_mode, self.__toggle_high_contrast_mode, 'Color Blind Mode', 'High contrast colors')
        self.__draw_separator()
        self.__draw_footer()

        # event loop
        while not self.__closing:
            # NOTE: Using parent panel's size constraints as this panel's.
            k = self._input.get(parent_min_required_total_height,
                                parent_min_required_total_width)
