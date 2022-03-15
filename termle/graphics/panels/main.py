# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses
import _curses
import curses.panel
import math

from constants       import GAME_NAME_STYLIZED
from gamecore        import LetterStatus, GuessResult
from shareablestatus import ShareableStatus

from ..           import glyphs
from ..exceptions import WindowResized
from ..modalpanel import ModalPanel

from .help      import HelpPanel
from .playstats import PlayStatsPanel
from .settings  import SettingsPanel
from .toast     import Toast

class MainPanel(ModalPanel):

    # NOTE: These are all tweakable, but have undocumented constraints that the
    #        code may or may not check for.  Don't be surprised if certain
    #        values result in errant behavior.
    #
    __TILE_LETTER_PLACEHOLDER = 'A'
    #
    # Tiles:
    #   - each tile contains 1-2 types of characters:
    #       - letter character (only in certain modes), appears in definitions
    #          below as a placeholder which will be replaced at runtime
    #       - border characters (i.e. everything else)
    #   - should ideally have odd height and width, so that letter is centered
    #   - consist of multiple modes (all except 'blink' are required), each of
    #      which implies certain color pairs to render with:
    #       - 'blank' ───────────────▷ all characters:    'border_blank'
    #       - 'unsubmitted' ────────┬▷ letter character:  'letter_unsubmitted'
    #                               └▷ border characters: 'border_unsubmitted'
    #       - 'blink' ───────────────▷ all characters:    'border_unsubmitted'
    #       - LetterStatus.*.value ─┬▷ if all border chars are spaces:
    #                               │   │(see (*) for explanation)
    #                               │   └▷ all characters: 'letter_'+status
    #                               └▷ otherwise:
    #                                   ├▷ letter character:  'letter_'+status
    #                                   └▷ border characters: 'border_'+status
    #   - if optional 'blink'-mode tile present, will be displayed during tile
    #      flipping, between 'unsubmitted' tile and LetterStatus.*.value tile
    __TILE_NORMAL = {'blank':                      ('\u250c\u2500\u2500\u2500\u2510',  # ┌───┐
                                                    '\u2502   \u2502',                 # │   │
                                                    '\u2514\u2500\u2500\u2500\u2518'), # └───┘
                     'unsubmitted':                ('\u250c\u2500\u2500\u2500\u2510',  # ┌───┐
                                                    '\u2502 A \u2502',                 # │ A │
                                                    '\u2514\u2500\u2500\u2500\u2518'), # └───┘
                     'blink':                      ('     ',                           #
                                                    '\u2576\u2500\u2500\u2500\u2574',  # ╶───╴
                                                    '     '),                          #
                     LetterStatus.WRONG.value:     ('\u2597\u2584\u2584\u2584\u2596',  # ▗▄▄▄▖ ⎫
                                                    '\u2590\u2588A\u2588\u258c',       # ▐█A█▌ ⎪
                                                    '\u259d\u2580\u2580\u2580\u2598'), # ▝▀▀▀▘ ⎪
                     LetterStatus.MISPLACED.value: ('\u2597\u2584\u2584\u2584\u2596',  # ▗▄▄▄▖ ⎪ Letter bg color will be same as
                                                    '\u2590\u2588A\u2588\u258c',       # ▐█A█▌ ⎬  block chars' fg color, giving
                                                    '\u259d\u2580\u2580\u2580\u2598'), # ▝▀▀▀▘ ⎪  appearance of a solid box.
                     LetterStatus.RIGHT.value:     ('\u2597\u2584\u2584\u2584\u2596',  # ▗▄▄▄▖ ⎪
                                                    '\u2590\u2588A\u2588\u258c',       # ▐█A█▌ ⎪
                                                    '\u259d\u2580\u2580\u2580\u2598')} # ▝▀▀▀▘ ⎭
    __TILE_SMALL = {'blank':                      ('[_]',               ), # [_]
                    'unsubmitted':                ('[A]',               ), # [A]
                    'blink':                      ('\u2576\u2500\u2574',), # ╶─╴
                    LetterStatus.WRONG.value:     (' A ',               ), #  A  ⎫ When rendered, these will look
                    LetterStatus.MISPLACED.value: (' A ',               ), #  A  ⎬  similar to █A█ but with letter
                    LetterStatus.RIGHT.value:     (' A ',               )} #  A  ⎭  filled in.  See (*) below.
    # Some other borders considered, for reference:
    #   Width 1:
    #     '\u2395'             ⎕
    #     '\u23b5'             ⎵
    #   Width 3:
    #     3*'\u2581'           ▁▁▁
    #     3*'_'                    ___
    #     '\u23a3\u2581\u23a6' ⎣▁⎦
    #     '\u23a3_\u23a6'          ⎣_⎦
    #     '\u23a9_\u23ad'      ⎩_⎭
    #     '\uff62 \uff63'          ｢ ｣
    #     '\u231e \u231f'      ⌞ ⌟
    #     '\u2e24 \u2e25'          ⸤ ⸥
    #     3*'\u2588'           ███
    #     3*'\u2591'               ░░░
    #     3*'\u2592'           ▒▒▒
    #     3*'\u2593'               ▓▓▓
    #
    __TILES_NORMAL_GAP_X = 1 # spaces between horizontally adjacent normal tiles
    __TILES_NORMAL_GAP_Y = 0 # blank lines between rows of normal tiles
    __TILES_SMALL_GAP_X  = 1 # spaces between horizontally adjacent small tiles
    __TILES_SMALL_GAP_Y  = 1 # blank lines between rows of small tiles
    #
    __TILE_FLIP_DELAY_MSEC = 400 # delay in milliseconds between each tile flip
    #
    __KB_KEY_STD_WIDTH     = 3                    # ideally an odd number
    __KB_KEY_SPECIAL_WIDTH = __KB_KEY_STD_WIDTH+2 # ideally an odd number
    __KB_ROW_HEIGHT        = 1                    # ideally an odd number
    __KB_GAP_X             = 1                    # spaces between horizontally adjacent keys
    __KB_GAP_Y             = 1                    # blank lines between rows of keys
    #
    __KB_ROWS = [# Q   W   E   R   T   Y   U   I   O   P
                 #
                 #   A   S   D   F   G   H   J   K   L
                 #
                 #  ↵    Z   X   C   V   B   N   M    ⌫
                 {'x_offset': 0, 'keys': [#glyph:                code:            width:
                                          ('Q',                  'q',             __KB_KEY_STD_WIDTH),
                                          ('W',                  'w',             __KB_KEY_STD_WIDTH),
                                          ('E',                  'e',             __KB_KEY_STD_WIDTH),
                                          ('R',                  'r',             __KB_KEY_STD_WIDTH),
                                          ('T',                  't',             __KB_KEY_STD_WIDTH),
                                          ('Y',                  'y',             __KB_KEY_STD_WIDTH),
                                          ('U',                  'u',             __KB_KEY_STD_WIDTH),
                                          ('I',                  'i',             __KB_KEY_STD_WIDTH),
                                          ('O',                  'o',             __KB_KEY_STD_WIDTH),
                                          ('P',                  'p',             __KB_KEY_STD_WIDTH)]},
                 {'x_offset': 2, 'keys': [('A',                  'a',             __KB_KEY_STD_WIDTH),
                                          ('S',                  's',             __KB_KEY_STD_WIDTH),
                                          ('D',                  'd',             __KB_KEY_STD_WIDTH),
                                          ('F',                  'f',             __KB_KEY_STD_WIDTH),
                                          ('G',                  'g',             __KB_KEY_STD_WIDTH),
                                          ('H',                  'h',             __KB_KEY_STD_WIDTH),
                                          ('J',                  'j',             __KB_KEY_STD_WIDTH),
                                          ('K',                  'k',             __KB_KEY_STD_WIDTH),
                                          ('L',                  'l',             __KB_KEY_STD_WIDTH)]},
                 {'x_offset': 0, 'keys': [(glyphs.ENTER_KEY,     '\n',            __KB_KEY_SPECIAL_WIDTH),
                                          ('Z',                  'z',             __KB_KEY_STD_WIDTH),
                                          ('X',                  'x',             __KB_KEY_STD_WIDTH),
                                          ('C',                  'c',             __KB_KEY_STD_WIDTH),
                                          ('V',                  'v',             __KB_KEY_STD_WIDTH),
                                          ('B',                  'b',             __KB_KEY_STD_WIDTH),
                                          ('N',                  'n',             __KB_KEY_STD_WIDTH),
                                          ('M',                  'm',             __KB_KEY_STD_WIDTH),
                                          (glyphs.BACKSPACE_KEY, 'KEY_BACKSPACE', __KB_KEY_SPECIAL_WIDTH)]}]
    #
    __ORDINALS = ('1st', '2nd', '3rd', '4th', '5th')
    __CONGRATULATORY_TOASTS = ['Genius',
                               'Magnificent',
                               'Impressive',
                               'Splendid',
                               'Great',
                               'Phew']

    def __init__(self,
                 stdscr,
                 colors,
                 game_core,
                 config,
                 game_num_str=None):

        super().__init__(stdscr, colors)

        self.__game_core                               = game_core
        self.__config                                  = config
        self.__game_num_str                            = game_num_str
        self.__header_start_y                          = None
        self.__header_start_x                          = None
        self.__header_height                           = None
        self.__header_width                            = None
        self.__game_title_lines                        = GAME_NAME_STYLIZED[:] # shallow copy the list (each element is immutable so no need to deep copy)
        self.__game_title_width                        = None
        self.__game_title_start_x                      = None
        self.__active_tile_def                         = None
        self.__tiles_y                                 = None
        self.__tiles_x                                 = None
        self.__use_letter_status_color_for_entire_tile = None
        self.__kb_start_y                              = None
        self.__kb_start_x                              = None
        #
        self.__leftmost_x                              = None
        self.__widest                                  = None
        #
        self.__min_required_total_height               = None
        self.__min_required_total_width                = None

    def __init_size_calculations(self, jump_to_panel):

        def tile_calculations_and_assertions(tile_def,
                                             tiles_gap_y,
                                             tiles_gap_x):

            # set of unique line counts, from each tile mode
            unique_tile_heights = {len(tile_mode_lines)
                                   for tile_mode_lines in tile_def.values()}

            # set of unique line lengths, from each line of each tile mode
            unique_tile_widths = {len(line)
                                  for tile_mode_lines in tile_def.values()
                                  for line in tile_mode_lines}

            # all tiles across all modes must have same number of lines
            assert len(unique_tile_heights)==1

            # all tile lines across all modes must have same lengths
            assert len(unique_tile_widths)==1

            # calculate individual and total heights and widths
            tile_height        = unique_tile_heights.pop()
            tile_width         = unique_tile_widths.pop()
            tiles_total_height = tile_height * self.__game_core.MAX_GUESSES + tiles_gap_y * (self.__game_core.MAX_GUESSES-1)
            tiles_total_width  = tile_width  * self.__game_core.WORD_LENGTH + tiles_gap_x * (self.__game_core.WORD_LENGTH-1)

            # "blank" and "blink" tile modes must have no letter placeholder
            assert all(sum(line.count(self.__TILE_LETTER_PLACEHOLDER)
                           for line in tile_lines)==0
                       for mode,tile_lines in tile_def.items()
                       if mode in ['blank', 'blink'])

            # all tile modes other than "blank" and "blink" must have exactly 1
            #  letter placeholder
            assert all(sum(line.count(self.__TILE_LETTER_PLACEHOLDER)
                           for line in tile_lines)==1
                       for mode,tile_lines in tile_def.items()
                       if mode not in ['blank', 'blink'])

            return (tile_height, tile_width, tiles_total_height, tiles_total_width)

        # perform calculations and assertions for game title
        unique_game_title_line_widths = {len(game_title_line)
                                         for game_title_line
                                          in self.__game_title_lines}
        assert len(unique_game_title_line_widths)==1
        self.__game_title_width = unique_game_title_line_widths.pop()

        # perform calculations and assertions for each tile size
        #  (we don't yet know which size will be used)
        (tile_normal_height,
         tile_normal_width,
         tiles_normal_total_height,
         tiles_normal_total_width) = tile_calculations_and_assertions(self.__TILE_NORMAL,
                                                                      self.__TILES_NORMAL_GAP_Y,
                                                                      self.__TILES_NORMAL_GAP_X)
        (tile_small_height,
         tile_small_width,
         tiles_small_total_height,
         tiles_small_total_width)  = tile_calculations_and_assertions(self.__TILE_SMALL,
                                                                      self.__TILES_SMALL_GAP_Y,
                                                                      self.__TILES_SMALL_GAP_X)
        assert tile_normal_height        >= tile_small_height
        assert tile_normal_width         >= tile_small_width
        assert tiles_normal_total_height >= tiles_small_total_height
        assert tiles_normal_total_width  >= tiles_small_total_width

        # lists of ordinals and congratulatory toasts must match game
        #  parameters
        assert len(self.__ORDINALS) >= self.__game_core.WORD_LENGTH
        assert len(self.__CONGRATULATORY_TOASTS) >= self.__game_core.MAX_GUESSES

        # precalculate everything needed for rendering
        #
        # entire window:
        (rows, cols) = self._win.getmaxyx()
        #
        # header:
        self.__header_start_y = 0
        self.__header_height  = len(self.__game_title_lines)+1
        if len(self.__game_title_lines)==1 and self.__game_title_width%2==0:
            # space out even-lengthed title to make it odd, so it can be centered
            self.__game_title_lines[0] = ' '.join(self.__game_title_lines[0])
            self.__game_title_width = len(self.__game_title_lines[0])
        self.__game_title_start_x = cols//2 - self.__game_title_width//2
        #
        # keyboard:
        kb_height  = (  len(self.__KB_ROWS) * self.__KB_ROW_HEIGHT
                      + (len(self.__KB_ROWS)-1) * self.__KB_GAP_Y)
        kb_width   = max(  sum(key_spec[2] for key_spec in row['keys'])
                         + (len(row['keys'])-1) * self.__KB_GAP_X
                         for row in self.__KB_ROWS)
        self.__kb_start_y = rows - kb_height
        self.__kb_start_x = cols//2 - kb_width//2
        #
        # tiles:
        avail_height_for_tiles = (  rows
                                  - self.__header_start_y
                                  - self.__header_height
                                  - kb_height)
        avail_width_for_tiles  = cols
        for (tile_def,
             tiles_gap_y,
             tiles_gap_x,
             tile_height,
             tile_width,
             tiles_total_height,
             tiles_total_width) in ((self.__TILE_NORMAL,
                                     self.__TILES_NORMAL_GAP_Y,
                                     self.__TILES_NORMAL_GAP_X,
                                     tile_normal_height,
                                     tile_normal_width,
                                     tiles_normal_total_height,
                                     tiles_normal_total_width),
                                    (self.__TILE_SMALL,
                                     self.__TILES_SMALL_GAP_Y,
                                     self.__TILES_SMALL_GAP_X,
                                     tile_small_height,
                                     tile_small_width,
                                     tiles_small_total_height,
                                     tiles_small_total_width)):
            # skip to next tile definition if this one won't fit:
            if (   avail_height_for_tiles < tiles_total_height
                or avail_width_for_tiles < tiles_total_width):
                continue

            # record selected tile definition:
            self.__active_tile_def = tile_def

            # y coordinates:
            tiles_start_y  = (  self.__header_start_y
                              + self.__header_height
                              + (avail_height_for_tiles-tiles_total_height)//2)
            self.__tiles_y = [  tiles_start_y
                              + (tile_height+tiles_gap_y) * g
                              for g in range(self.__game_core.MAX_GUESSES)]

            # x coordinates:
            if self.__game_core.WORD_LENGTH%2 == 0:
                # gap between middle two tiles (i.e. tile_index==-1 (left of center)
                #  and tile_index==0 (right of center)) should be centered
                offset_from_center_for_tile_index_0 = tiles_gap_x//2+1
            else:
                # middle tile (i.e. tile_index==0) should be centered
                offset_from_center_for_tile_index_0 = -(tile_width//2)
            self.__tiles_x = [  cols//2
                              + offset_from_center_for_tile_index_0
                              + (tile_width+tiles_gap_x) * tile_index
                              for tile_index in range(-(self.__game_core.WORD_LENGTH//2),
                                                      math.ceil(self.__game_core.WORD_LENGTH/2))]

            break
        #
        # calculate min. required terminal size, notify player to resize if unmet
        self.__min_required_total_height = (  self.__header_start_y
                                            + self.__header_height
                                            + tiles_small_total_height
                                            + kb_height)
        self.__min_required_total_width  = max(self.__game_title_width,
                                               tiles_small_total_width,
                                               kb_width)
        if (   rows < self.__min_required_total_height
            or cols < self.__min_required_total_width):
            raise WindowResized(rows,
                                cols,
                                self.__min_required_total_height,
                                self.__min_required_total_width,
                                jump_to_panel or self.__class__.__name__)
        #
        # if min size met (above), tiles must be defined by now:
        assert self.__active_tile_def is not None
        #
        # overall:
        self.__leftmost_x = min(self.__tiles_x[0], self.__kb_start_x)
        self.__widest     = max(self.__game_title_width,
                                tiles_total_width,
                                kb_width)
        #
        # header:
        self.__header_start_x = self.__leftmost_x
        self.__header_width   = self.__widest

        # If all border chars, for all LetterStatus.*.value mode tiles, are
        #  spaces, use color pair 'letter_'+status instead of
        #  'border_'+status.
        # (*) NOTE: After support was added to this program for the more
        #            complex multi-line tiles, this logic was necessary in
        #            order to keep the code reasonably generic while
        #            retaining the ability to properly render the simpler
        #            single-line tiles (which originally were the only kind
        #            of tiles this program supported).  The simpler tiles
        #            are still used, if the larger tiles don't fit.
        #           In the initial implementation, simpler tiles didn't
        #            formally have modes, they effectively only had a
        #            "blank" mode.  So if the tile was "[_]", after an 'A'
        #            was typed it would look like " A ", and after a guess
        #            was submitted and the tiles redrawn, that entire " A "
        #            would be drawn with the letter's status color used as
        #            the background color.  In other words it would form a
        #            rectangular block with nice straight edges.
        #           The implementation of complex tiles, however, calls for
        #            all border characters (i.e. everything other than the
        #            letter) to be drawn using the letter's status color as
        #            the *foreground* color, and for the background use the
        #            game board's background color.  This meant that spaces
        #            could no longer be used around the letter (i.e. " A ")
        #            and it would have to be some glyph that would fill an
        #            entire cell.  The only such glyph that was found was
        #            U+2588 (i.e. █), but the problem was it was rendered
        #            with 1 less pixel row (on the bottom) than the letter
        #            with its background color.  This meant that the tile
        #            did not appear to have nice straight edges.  Therefore
        #            this compromise was created.  If all the
        #            LetterStatus.*.value modes' tiles' border characters
        #            are spaces (which they are for the simple (smaller)
        #            tile), then render those spaces using the letter
        #            status color as a background color, not as a
        #            foreground color.
        self.__use_letter_status_color_for_entire_tile = {c
                                                          for s in LetterStatus
                                                          for line in self.__active_tile_def[s.value]
                                                          for c in line
                                                          if c!=self.__TILE_LETTER_PLACEHOLDER} == {' '}

        # in case of faulty logic above, assert each individual requirement
        assert self.__header_start_y                             >= 0
        assert self.__header_start_x                             >= 0
        assert self.__game_title_start_x                         >= 0
        assert self.__tiles_x[0]                                 >= 0
        assert self.__kb_start_y                                 >= self.__tiles_y[-1]+tile_height
        assert self.__kb_start_x                                 >= 0
        #
        assert self.__kb_start_y+kb_height                       <= rows
        assert self.__kb_start_x+kb_width                        <= cols
        assert self.__tiles_x[-1]+tile_width                     <= cols
        assert self.__game_title_start_x+self.__game_title_width <= cols
        assert self.__header_start_x+self.__header_width         <= cols

    def __draw_header(self):

        # game title and header line
        for y_offset,line in enumerate(self.__game_title_lines):
            self._win.addstr(self.__header_start_y + y_offset,
                             self.__game_title_start_x,
                             line,
                             curses.A_BOLD|self._colors.attr('text_default'))
        self._win.addstr(self.__header_start_y+len(self.__game_title_lines),
                         self.__header_start_x,
                         self.__header_width*glyphs.HORIZONTAL_LINE_SEGMENT,
                         self._colors.attr('separator_line'))

        buttons_y = len(self.__game_title_lines)//2

        # help button
        # NOTE: This is a double-width character, but the glyph is mostly in
        #        the left half of the allotted space, so we still only use a
        #        width of 1 for the click region.
        help_x = self.__header_start_x
        self._win.addstr(buttons_y,
                         help_x,
                         glyphs.HELP_BUTTON,
                         self._colors.attr('header_button'))
        self._input.add_to_click_map(buttons_y,
                                     help_x,
                                     1,
                                     1,
                                     self.__help_panel)

        # stats button
        # NOTE: This is a double-width character, so we must subtract 3
        #        (instead of 2), and use a width of 2 for the click region.
        if self.__game_core.play_stats is not None:
            stats_x = self.__header_start_x+self.__header_width-3
            self._win.addstr(buttons_y,
                             stats_x,
                             glyphs.STATS_BUTTON,
                             self._colors.attr('header_button'))
            self._input.add_to_click_map(buttons_y,
                                         stats_x,
                                         1,
                                         2,
                                         self.__play_stats_panel)

        # settings button
        settings_x = self.__header_start_x+self.__header_width-1
        self._win.addstr(buttons_y,
                         settings_x,
                         glyphs.SETTINGS_BUTTON,
                         self._colors.attr('header_button'))
        self._input.add_to_click_map(buttons_y,
                                     settings_x,
                                     1,
                                     1,
                                     self.__settings_panel)

    def __draw_tile(self, y, x, mode, letter=' '):
        if mode == 'unsubmitted':
            letter_attr = self._colors.attr(f'letter_{mode}')
            border_attr = self._colors.attr(f'border_{mode}')
        elif mode in {s.value for s in LetterStatus}:
            letter_attr = self._colors.attr(f'letter_{mode}')
            border_attr = (letter_attr
                           if self.__use_letter_status_color_for_entire_tile else
                           self._colors.attr(f'border_{mode}'))
        else:
            letter_attr = None
            border_attr = self._colors.attr(f'border_{mode}')
        for y_offset,line in enumerate(self.__active_tile_def[mode]):
            border_segments = line.split(self.__TILE_LETTER_PLACEHOLDER, 1)
            self._win.addstr(y+y_offset,
                             x,
                             border_segments[0],
                             border_attr)
            if len(border_segments) == 2:
                self._win.addstr(y+y_offset,
                                 x+len(border_segments[0]),
                                 letter,
                                 curses.A_BOLD|letter_attr)
                self._win.addstr(y+y_offset,
                                 x+len(border_segments[0])+1,
                                 border_segments[1],
                                 border_attr)

    def __draw_guess(self, index, guess, tile_flip_delay_msec=0): # will refresh between each letter if delay>0, else caller must refresh (note that things like w.getch() and w.getkey() seem to automatically do w.refresh() on window w (getkey does so *before* waiting for the key))
        fancy_auto_mode = tile_flip_delay_msec>0
        do_animation = fancy_auto_mode and 'blink' in self.__active_tile_def
        delay_msec = tile_flip_delay_msec//(2 if do_animation else 1)
        for i,(letter,letter_status) in enumerate(zip(guess['word'].upper(), guess['letter_statuses'])):
            if fancy_auto_mode and i>0:
                curses.napms(delay_msec)
            if do_animation:
                self.__draw_tile(self.__tiles_y[index],
                                 self.__tiles_x[i],
                                 'blink')
                self._win.refresh()
                curses.napms(delay_msec)
            self.__draw_tile(self.__tiles_y[index],
                             self.__tiles_x[i],
                             letter_status.value,
                             letter)
            if fancy_auto_mode:
                self._win.refresh()

    def __draw_keyboard(self):
        pad_height_top = (self.__KB_ROW_HEIGHT-1)//2
        pad_height_bottom = self.__KB_ROW_HEIGHT-1-pad_height_top
        for r,kb_row in enumerate(self.__KB_ROWS):
            row_start_y = (  self.__kb_start_y
                           + r*(self.__KB_ROW_HEIGHT+self.__KB_GAP_Y))
            x = self.__kb_start_x + kb_row['x_offset']
            for key_glyph,key_code,key_width in kb_row['keys']:
                self._input.add_to_click_map(row_start_y,
                                             x,
                                             self.__KB_ROW_HEIGHT,
                                             key_width,
                                             key_code)
                pad_width_left = (key_width-len(key_glyph))//2
                pad_width_right = key_width-len(key_glyph)-pad_width_left
                key_letter_status = self.__game_core.letter_status(key_code)
                if key_letter_status is None:
                    key_attr = self._colors.attr('unguessed')
                else:
                    key_attr = self._colors.attr(f'letter_{key_letter_status.value}')
                for y_offset in range(pad_height_top):
                    self._win.addstr(row_start_y + y_offset,
                                     x,
                                     key_width*' ',
                                     key_attr)
                try:
                    # either of the following addstr calls may run into
                    #  https://stackoverflow.com/questions/36387625, so we
                    #  catch the exception and ignore it
                    self._win.addstr(row_start_y + pad_height_top,
                                     x,
                                     f'{pad_width_left*" "}{key_glyph}{pad_width_right*" "}',
                                     key_attr)
                    for y_offset in range(pad_height_bottom):
                        self._win.addstr(row_start_y + pad_height_top + 1 + y_offset,
                                         x,
                                         key_width*' ',
                                         key_attr)
                except _curses.error:
                    pass
                x += self.__KB_GAP_X+key_width

    def __full_draw(self):
        self._win.bkgd(self._colors.attr('background'))
        self.__draw_header()
        for g in range(self.__game_core.MAX_GUESSES):
            if g < len(self.__game_core.guesses):
                self.__draw_guess(g, self.__game_core.guesses[g])
            else:
                for i in range(self.__game_core.WORD_LENGTH):
                    if (    g == len(self.__game_core.guesses)
                        and i < len(self.__game_core.pending_guess_letters)):
                        self.__draw_tile(self.__tiles_y[g],
                                         self.__tiles_x[i],
                                         'unsubmitted',
                                         self.__game_core.pending_guess_letters[i].upper())
                    else:
                        self.__draw_tile(self.__tiles_y[g],
                                         self.__tiles_x[i],
                                         'blank')
        self.__draw_keyboard()

    def __help_panel(self):
        pass

    def __play_stats_panel(self):
        shareable_status = ShareableStatus(self.__game_core,
                                           self.__game_num_str,
                                           self.__config)
        play_stats_panel = PlayStatsPanel(self._stdscr,
                                          self._colors,
                                          self.__game_core,
                                          shareable_status)
        self._colors.dim()
        self.__full_draw()
        play_stats_panel.run(parent_min_required_total_height = self.__min_required_total_height,
                             parent_min_required_total_width  = self.__min_required_total_width)
        self._colors.undim()
        self.__full_draw()

    def __settings_panel(self):
        settings_panel = SettingsPanel(self._stdscr,
                                       self._colors,
                                       self.__config,
                                       self.__game_core,
                                       self.__game_num_str)
        settings_panel.run(height=self._stdscr.getmaxyx()[0],
                           width=self.__widest,
                           start_y=0,
                           start_x=self.__leftmost_x,
                           parent_min_required_total_height = self.__min_required_total_height,
                           parent_min_required_total_width  = self.__min_required_total_width)

    def _run(self, jump_to_panel):

        self.__init_size_calculations(jump_to_panel)

        # set background and perform initial drawing
        self.__full_draw()

        if jump_to_panel:
            panels = {panel_class.__name__: panel_launcher
                      for (panel_class, panel_launcher)
                       in ((HelpPanel,      self.__help_panel),
                           (PlayStatsPanel, self.__play_stats_panel),
                           (SettingsPanel,  self.__settings_panel))}
            if jump_to_panel in panels:
                panels[jump_to_panel]()

        if not self.__game_core.is_completed():
            # event loops
            #   outermost loop (for loop) is "guess loop"
            #   nested loop (while loop) is "letter loop"
            #   innermost loop (while loop) is "input loop"
            for g in range(len(self.__game_core.guesses),
                           self.__game_core.MAX_GUESSES):
                # BODY OF GUESS LOOP: BEGIN
                guess_result = None
                i = len(self.__game_core.pending_guess_letters)
                while i < self.__game_core.WORD_LENGTH+1: # +1 for an extra iteration to handle player hitting enter or backspace after typing entire word
                    # BODY OF LETTER LOOP: BEGIN
                    k = self._input.get(self.__min_required_total_height,
                                        self.__min_required_total_width)
                    if k == '~':
                        return
                    if k == 'KEY_BACKSPACE' and i > 0:
                        i -= 1
                        self.__draw_tile(self.__tiles_y[g],
                                         self.__tiles_x[i],
                                         'blank')
                        self.__game_core.remove_last_letter_from_pending_guess()
                    elif k and len(k) == 1 and k.isalpha() and i < self.__game_core.WORD_LENGTH:
                        l = k.upper()
                        if self.__game_core.append_letter_to_pending_guess(l):
                            self.__draw_tile(self.__tiles_y[g],
                                             self.__tiles_x[i],
                                             'unsubmitted',
                                             l)
                            i += 1
                    elif k == '\n':
                        (guess_result,
                         first_offending_letter,
                         first_offending_position) = self.__game_core.submit_pending_guess()
                        if guess_result in (GuessResult.WRONG,
                                            GuessResult.WRONG_AND_GAME_OVER,
                                            GuessResult.RIGHT):
                            self.__draw_guess(g, self.__game_core.guesses[-1], self.__TILE_FLIP_DELAY_MSEC)
                            self.__draw_keyboard()
                            curses.flushinp() # drop any keystrokes made by player during __draw_guess()'s "animation"
                            i += 1
                        elif guess_result in (GuessResult.INVALID_TOO_SHORT,
                                              GuessResult.INVALID,
                                              GuessResult.INVALID_HARD_MODE_MISSING_PREV_GUESS_MISPLACED_LETTER,
                                              GuessResult.INVALID_HARD_MODE_MISSING_PREV_GUESS_CORRECT_LETTER):
                            if guess_result == GuessResult.INVALID_TOO_SHORT:
                                toast_text = 'Not enough letters'
                            elif guess_result == GuessResult.INVALID:
                                toast_text = 'Not in word list'
                            elif guess_result == GuessResult.INVALID_HARD_MODE_MISSING_PREV_GUESS_MISPLACED_LETTER:
                                toast_text = f'Guess must contain {first_offending_letter.upper()}'
                            elif guess_result == GuessResult.INVALID_HARD_MODE_MISSING_PREV_GUESS_CORRECT_LETTER:
                                toast_text = (f'{self.__ORDINALS[first_offending_position]}'
                                              f' letter must be {first_offending_letter.upper()}')
                            else:
                                toast_text = None
                            if toast_text:
                                toast = Toast(self._stdscr, self._colors)
                                toast.run(toast_text)
                    # BODY OF LETTER LOOP: END
                if guess_result == GuessResult.RIGHT:
                    break
                # BODY OF GUESS LOOP: END

            if guess_result == GuessResult.WRONG_AND_GAME_OVER:
                answer = self.__game_core.answer()
                if not answer:
                    pass
                else:
                    toast = Toast(self._stdscr, self._colors)
                    toast.run(answer.upper())
                if self.__game_core.play_stats is not None:
                    self.__play_stats_panel()
            elif guess_result == GuessResult.RIGHT:
                toast = Toast(self._stdscr, self._colors)
                toast.run(self.__CONGRATULATORY_TOASTS[len(self.__game_core.guesses)-1])
                if self.__game_core.play_stats is not None:
                    self.__play_stats_panel()

        # end state event loop (game is over, but player can still interact)
        while True:
            k = self._input.get(self.__min_required_total_height,
                                self.__min_required_total_width)
            if k == '~': return
