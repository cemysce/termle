# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses
import decimal
import math

from gamecore import LetterStatus

class Colors:

    @staticmethod
    def apply_alpha(c, bg, alpha):
        return alpha*c + (1-alpha)*bg

    @classmethod
    def rgb_half_opaque(cls, rgb, dark=False):
        alpha = 0.5
        if dark:
            bg = 0
            quantize = math.floor
        else:
            def int_round_traditional(f):
                return int(decimal.Decimal(f).quantize(decimal.Decimal('1'),
                                                       rounding=decimal.ROUND_HALF_UP))
            bg = 255
            quantize = int_round_traditional
        return tuple(quantize(cls.apply_alpha(c, bg, alpha)) for c in rgb)

    # NOTE: The names may imply each color is only used for one purpose but in
    #        fact they may be used for multiple things.  Since there is a limit
    #        on the number of colors that can be registered with ncurses, we
    #        only have 1 definition per unique color set (i.e. across all 4
    #        modes).  Color pairs, however, are a different story (see comment
    #        above _COLOR_PAIRS definition).
    _COLORS = {#color name                    normal         dark           high contrast  dark high contrast
               'border_blank':               [(211,214,218), ( 58, 58, 60), (211,214,218), ( 58, 58, 60)],
               'border_unsubmitted':         [(135,138,140), ( 86, 87, 88), (135,138,140), ( 86, 87, 88)],
               'letter_unsubmitted':         [( 26, 26, 27), (215,218,220), ( 26, 26, 27), (215,218,220)],
               'letter_submitted':           [(255,255,255), (215,218,220), (255,255,255), (255,255,255)],
               'background':                 [(255,255,255), ( 18, 18, 19), (255,255,255), ( 18, 18, 19)],
               'unguessed':                  [(211,214,218), (129,131,132), (211,214,218), (129,131,132)],
               LetterStatus.WRONG.value:     [(120,124,126), ( 58, 58, 60), (120,124,126), ( 58, 58, 60)],
               LetterStatus.MISPLACED.value: [(201,180, 88), (181,159, 59), (133,192,249), (133,192,249)],
               LetterStatus.RIGHT.value:     [(106,170,100), ( 83,141, 78), (245,121, 58), (245,121, 58)],
               'subtext':                    [(120,124,126), (129,131,132), (120,124,126), (129,131,132)],
               'switch_off':                 [(135,138,140), (255,255,255), (135,138,140), (255,255,255)],
               'switch_off_insensitive':     [(195,196,197), (136,136,137), (195,196,197), (136,136,137)],
               'switch_off_gap_insensitive': [(195,196,197), ( 52, 52, 53), (195,196,197), ( 52, 52, 53)],
               'switch_on':                  [(106,170,100), (255,255,255), (245,121, 58), (255,255,255)],
               'share_button':               [(255,255,255), (215,218,220), (255,255,255), (215,218,220)],
               'share_button_icon':          [(255,255,255), (255,255,255), (255,255,255), (255,255,255)]}

    # NOTE: There is also a limit on the number of color pairs that can be
    #        registered with ncurses, but since the names of these pairs will
    #        have to appear throughout the code, it was decided that they
    #        should be meaningful in order to keep the code readable, which
    #        means there may be multiple pairs with the same definition if
    #        they're used for very different purposes that did not make sense
    #        to combine into a single entry.
    _COLOR_PAIRS = {#color pair name                          fg color name                 bg color name
                    'text_default':                          ('letter_unsubmitted',         'background'),
                    'subtext':                               ('subtext',                    'background'),
                    'header_button':                         ('border_unsubmitted',         'background'),
                    'separator_line':                        ('border_blank',               'background'),
                    'background':                            ('background',                 'background'),
                    'border_blank':                          ('border_blank',               'background'),
                    'border_unsubmitted':                    ('border_unsubmitted',         'background'),
                    'border_blink':                          ('border_unsubmitted',         'background'),
                   f'border_{LetterStatus.WRONG.value}':     (LetterStatus.WRONG.value,     'background'),
                   f'border_{LetterStatus.MISPLACED.value}': (LetterStatus.MISPLACED.value, 'background'),
                   f'border_{LetterStatus.RIGHT.value}':     (LetterStatus.RIGHT.value,     'background'),
                    'letter_unsubmitted':                    ('letter_unsubmitted',         'background'),
                    'unguessed':                             ('letter_unsubmitted',         'unguessed'),
                   f'letter_{LetterStatus.WRONG.value}':     ('letter_submitted',           LetterStatus.WRONG.value),
                   f'letter_{LetterStatus.MISPLACED.value}': ('letter_submitted',           LetterStatus.MISPLACED.value),
                   f'letter_{LetterStatus.RIGHT.value}':     ('letter_submitted',           LetterStatus.RIGHT.value),
                    'toast':                                 ('background',                 'letter_unsubmitted'),
                    'switch_off':                            ('switch_off',                 'background'),
                    'switch_off_gap':                        ('border_unsubmitted',         'background'),
                    'switch_off_insensitive':                ('switch_off_insensitive',     'background'),
                    'switch_off_gap_insensitive':            ('switch_off_gap_insensitive', 'background'),
                    'switch_on':                             ('switch_on',                  'background'),
                    'switch_on_gap':                         (LetterStatus.RIGHT.value,     'background'),
                    'bar_graph_today':                       (LetterStatus.RIGHT.value,     'background'),
                    'bar_graph':                             (LetterStatus.WRONG.value,     'background'),
                    'vertical_separator_line':               ('letter_unsubmitted',         'background'),
                    'share_button':                          ('share_button',               LetterStatus.RIGHT.value),
                    'share_button_icon':                     ('share_button_icon',          LetterStatus.RIGHT.value)}

    __DIMMED_SUFFIX = '__dimmed'

    def __init__(self, dark_mode, high_contrast_mode):

        self.__ncurses_color_pairs = {}
        self.__dimmed              = False

        style_index = int(dark_mode)+2*int(high_contrast_mode)

        # convert 0-255 RGB values in `_COLORS` (and their dimmed equivalents)
        #  to ncurses-style values and initialize ncurses colors
        ncurses_colors = {}
        color_number = 8 # 0 through 7 are already used
        for color_name_base, rgb_list in self._COLORS.items():
            for color_name, rgb in zip((color_name_base,
                                        color_name_base+self.__DIMMED_SUFFIX),
                                       (rgb_list[style_index],
                                        self.rgb_half_opaque(rgb_list[style_index],
                                                             dark_mode))):
                (nc_R, nc_G, nc_B) = tuple(c*1000//255
                                           for c in rgb)
                curses.init_color(color_number, nc_R, nc_G, nc_B)
                ncurses_colors[color_name] = color_number
                color_number += 1

        # initialize ncurses color pairs based on pairings defined in
        #  `_COLOR_PAIRS` (and their dimmed equivalents), and store pair
        #  numbers for later lookup
        pair_number = 1 # 0 is already used
        for pair_name, (fg_name, bg_name) in self._COLOR_PAIRS.items():
            for suffix in ('', self.__DIMMED_SUFFIX):
                curses.init_pair(pair_number,
                                 ncurses_colors[fg_name+suffix],
                                 ncurses_colors[bg_name+suffix])
                self.__ncurses_color_pairs[pair_name+suffix] = pair_number
                pair_number += 1

    def dim(self):
        self.__dimmed = True

    def undim(self):
        self.__dimmed = False

    def attr(self, color_pair_name):
        if self.__dimmed:
            color_pair_name += self.__DIMMED_SUFFIX
        return curses.color_pair(self.__ncurses_color_pairs[color_pair_name])
