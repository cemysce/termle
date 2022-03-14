# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses
import datetime

from math import ceil

import fancytext

from constants import GAME_NAME

from ..           import glyphs
from ..exceptions import WindowResized
from ..modalpanel import ModalPanel

from .toast import Toast

class PlayStatsPanel(ModalPanel):

    __BAR_LEFT   = '\u2597' # ▗
    __BAR_MIDDLE = '\u2584' # ▄
    __BAR_RIGHT  = '\u2596' # ▖

    __VERTICAL_SEPARATOR_TOP = '\u2577' # ╷
    __VERTICAL_SEPARATOR     = '\u2502' # │

    def __init__(self,
                 stdscr,
                 colors,
                 game_core,
                 shareable_status=None):
        super().__init__(stdscr, colors)
        self.__closing                    = None
        self.__game_core                  = game_core
        self.__shareable_status           = shareable_status
        self.__min_required_screen_height = None
        self.__min_required_screen_width  = None
        self.__stat_played_lines          = None
        self.__stat_winpct_lines          = None
        self.__stat_thisstreak_lines      = None
        self.__stat_maxstreak_lines       = None

    def __init_size_calculations(self):

        top_padding_height = 1

        self.__close_button_y = 0 + top_padding_height
        self.__close_button_height = 1
        self.__close_button_width = 1
        close_button_right_gap = 2

        self.__stats_heading = 'STATISTICS'
        self.__stats_heading_y = self.__close_button_y + self.__close_button_height
        stats_heading_height = 1
        stats_heading_width = len(self.__stats_heading)

        def gen_stat_text(value, subtext):
            (value_width, lines) = fancytext.bignum(str(int(value)),
                                                    calc_width=True)
            (label_width, label) = fancytext.superscript(subtext,
                                                         calc_width=True)
            gap = abs(value_width - label_width)
            pad_left = ceil(gap/2)*' '
            pad_right = (gap//2)*' '
            if value_width < label_width:
                lines = [pad_left + line + pad_right for line in lines]
            elif label_width < value_width:
                label = pad_left + label + pad_right
            lines.append(label)
            return (len(lines[0]), lines)

        (self.__stat_played_width,
         self.__stat_played_lines)     = gen_stat_text(self.__game_core.play_stats.num_completed(),
                                                       'Played')
        (self.__stat_winpct_width,
         self.__stat_winpct_lines)     = gen_stat_text(self.__game_core.play_stats.percent_won(),
                                                       'Win %')
        (self.__stat_thisstreak_width,
         self.__stat_thisstreak_lines) = gen_stat_text(self.__game_core.play_stats.current_streak(),
                                                       'This streak')
        (self.__stat_maxstreak_width,
         self.__stat_maxstreak_lines)  = gen_stat_text(self.__game_core.play_stats.max_streak(),
                                                       'Max streak')

        self.__stats_start_y = self.__stats_heading_y + stats_heading_height
        stats_label_height = 1
        stats_height = fancytext.BIGNUM_HEIGHT + stats_label_height
        inter_stat_gap_width = 2
        stats_width = (  self.__stat_played_width     + inter_stat_gap_width
                       + self.__stat_winpct_width     + inter_stat_gap_width
                       + self.__stat_thisstreak_width + inter_stat_gap_width
                       + self.__stat_maxstreak_width)

        post_stats_gap_height = 1

        self.__distribution_heading = 'GUESS DISTRIBUTION'
        self.__distribution_heading_y = self.__stats_start_y + stats_height + post_stats_gap_height
        distribution_heading_height = 1
        distribution_heading_width = len(self.__distribution_heading)

        if self.__game_core.play_stats.any_completed():
            self.__distribution_start_y = self.__distribution_heading_y + distribution_heading_height
            distribution_height = self.__game_core.MAX_GUESSES

            post_distribution_gap_height = 1

            if self.__game_core.is_completed():

                timer_heading_words = ['NEXT', GAME_NAME.upper()]
                timer_width = fancytext.bignum('00:00:00', calc_width=True)[0]
                self.__timer_heading = ' '.join(timer_heading_words)
                if len(self.__timer_heading)%2 != timer_width%2:
                    self.__timer_heading = '  '.join(timer_heading_words)
                self.__timer_heading_y = self.__distribution_start_y + distribution_height + post_distribution_gap_height
                timer_heading_height = 1
                timer_heading_width = len(self.__timer_heading)
                self.__timer_start_y = self.__timer_heading_y + timer_heading_height
                timer_height = fancytext.BIGNUM_HEIGHT
                timer_section_width = max(timer_heading_width, timer_width)

                self.__share_button_text = 'SHARE'
                share_button_text_len = len(self.__share_button_text)
                share_button_post_text_gap_width = 1
                share_button_display_str_len = share_button_text_len + share_button_post_text_gap_width + len(glyphs.SHARE_ICON)
                self.__share_button_start_y = self.__distribution_start_y + distribution_height + post_distribution_gap_height
                share_button_text_icon_height = 1
                share_button_pad_top_bottom = 1
                share_button_pad_left_right = 3
                self.__share_button_height = share_button_pad_top_bottom*2 + share_button_text_icon_height
                self.__share_button_width = share_button_pad_left_right*2 + share_button_display_str_len
                self.__share_button_text_icon_y = self.__share_button_start_y + share_button_pad_top_bottom

                timer_share_divider_line_gap_left_right = 1
                self.__timer_share_divider_line_start_y = self.__distribution_start_y + distribution_height
                self.__timer_share_divider_line_height = post_distribution_gap_height + max(timer_heading_height+timer_height, self.__share_button_height)
                timer_share_divider_line_width = 1
        else:
            post_distribution_heading_gap_height = 1
            self.__distribution_start_y = self.__distribution_heading_y + distribution_heading_height + post_distribution_heading_gap_height
            self.__distribution_no_data_str = 'No Data'
            distribution_height = 1

        bottom_padding_height = top_padding_height

        left_right_padding_width = 3

        if self.__game_core.play_stats.any_completed() and self.__game_core.is_completed():
            total_height = self.__timer_share_divider_line_start_y + self.__timer_share_divider_line_height + bottom_padding_height
            total_width = (  max(stats_heading_width,
                                 stats_width,
                                 distribution_heading_width,
                                 max(timer_section_width, self.__share_button_width)*2+2*timer_share_divider_line_gap_left_right)
                           + 2*left_right_padding_width)
        else:
            total_height = self.__distribution_start_y + distribution_height + bottom_padding_height
            total_width = (  max(stats_heading_width,
                                 stats_width,
                                 distribution_heading_width)
                           + 2*left_right_padding_width)

        self.__close_button_x = total_width - close_button_right_gap - self.__close_button_width

        self.__stats_heading_x = (total_width-stats_heading_width)//2

        self.__stat_played_start_x     = (total_width-stats_width)//2
        self.__stat_winpct_start_x     = self.__stat_played_start_x     + self.__stat_played_width     + inter_stat_gap_width
        self.__stat_thisstreak_start_x = self.__stat_winpct_start_x     + self.__stat_winpct_width     + inter_stat_gap_width
        self.__stat_maxstreak_start_x  = self.__stat_thisstreak_start_x + self.__stat_thisstreak_width + inter_stat_gap_width

        self.__distribution_heading_x = (total_width-distribution_heading_width)//2

        if self.__game_core.play_stats.any_completed():
            distribution_left_right_padding_width = left_right_padding_width + 1
            self.__distribution_start_x = distribution_left_right_padding_width
            self.__distribution_width = total_width - 2*distribution_left_right_padding_width

            if self.__game_core.is_completed():

                self.__timer_share_divider_line_x = total_width//2

                self.__timer_heading_start_x = (self.__timer_share_divider_line_x-timer_heading_width)//2
                self.__timer_start_x         = (self.__timer_share_divider_line_x-timer_width)//2

                self.__share_button_start_x = self.__timer_share_divider_line_x + timer_share_divider_line_width + (total_width-self.__timer_share_divider_line_x-timer_share_divider_line_width-self.__share_button_width)//2
                self.__share_button_text_start_x = self.__share_button_start_x + share_button_pad_left_right
                self.__share_button_icon_start_x = self.__share_button_text_start_x + share_button_text_len + share_button_post_text_gap_width
        else:
            self.__distribution_start_x = (total_width-len(self.__distribution_no_data_str))//2

        return (total_height, total_width)

    def __close(self):
        self.__closing = True

    def __share(self):
        toast = Toast(self._stdscr, self._colors)
        if self.__shareable_status is not None and self.__shareable_status.copy_to_clipboard():
            toast.run('Copied results to clipboard')
        else:
            toast.run('Share failed')

    def __draw_close_button(self):
        self._win.addstr(self.__close_button_y,
                         self.__close_button_x,
                         glyphs.X_BUTTON, # 🞩
                         self._colors.attr('header_button'))
        self._input.add_to_click_map(self.__close_button_y,
                                     self.__close_button_x,
                                     self.__close_button_height,
                                     self.__close_button_width,
                                     self.__close)

    def __draw_stat(self, start_x, lines):
        for y_offset, line in enumerate(lines):
            self._win.addstr(self.__stats_start_y+y_offset,
                             start_x,
                             line,
                             self._colors.attr('text_default'))

    def __draw_stats(self):
        self._win.addstr(self.__stats_heading_y,
                         self.__stats_heading_x,
                         self.__stats_heading,
                         curses.A_BOLD|self._colors.attr('text_default'))
        self.__draw_stat(self.__stat_played_start_x,     self.__stat_played_lines)
        self.__draw_stat(self.__stat_winpct_start_x,     self.__stat_winpct_lines)
        self.__draw_stat(self.__stat_thisstreak_start_x, self.__stat_thisstreak_lines)
        self.__draw_stat(self.__stat_maxstreak_start_x,  self.__stat_maxstreak_lines)

    def __draw_guess_bar(self, y, guess_num, is_today, max_guesses_len, bar_middle_width, count):
        self._win.addstr(y,
                         self.__distribution_start_x,
                         fancytext.subscript(str(guess_num)),
                         self._colors.attr('text_default'))
        self._win.addstr(y,
                         self.__distribution_start_x+max_guesses_len,
                         self.__BAR_LEFT+bar_middle_width*self.__BAR_MIDDLE+self.__BAR_RIGHT,
                         self._colors.attr('bar_graph_today'
                                           if is_today else
                                           'bar_graph'))
        self._win.addstr(y,
                         self.__distribution_start_x+max_guesses_len+len(self.__BAR_LEFT)+len(self.__BAR_RIGHT)+bar_middle_width,
                         fancytext.subscript(str(count)),
                         curses.A_BOLD|self._colors.attr('text_default'))

    def __draw_guess_distribution(self):
        self._win.addstr(self.__distribution_heading_y,
                         self.__distribution_heading_x,
                         self.__distribution_heading,
                         curses.A_BOLD|self._colors.attr('text_default'))
        if self.__game_core.play_stats.any_completed():
            distribution = self.__game_core.play_stats.guess_distribution()
            max_guesses = self.__game_core.MAX_GUESSES
            max_guesses_len = len(str(max_guesses))
            max_count = max(distribution.values())
            bar_middle_max_width = (  self.__distribution_width
                                    - len(str(max_guesses))
                                    - len(str(max_count))
                                    - len(self.__BAR_LEFT)
                                    - len(self.__BAR_RIGHT))
            today_winning_guess_num = None
            if self.__game_core.is_won():
                today_winning_guess_num = len(self.__game_core.guesses)
            for y_offset in range(max_guesses):
                guess_num = y_offset+1
                count = distribution[guess_num]
                bar_middle_width = 0
                if max_count > 0:
                    bar_middle_width = (count*bar_middle_max_width)//max_count
                self.__draw_guess_bar(self.__distribution_start_y+y_offset,
                                      guess_num,
                                      guess_num==today_winning_guess_num,
                                      max_guesses_len,
                                      bar_middle_width,
                                      count)
        else:
            self._win.addstr(self.__distribution_start_y,
                             self.__distribution_start_x,
                             self.__distribution_no_data_str,
                             self._colors.attr('text_default'))

    def __draw_timer_heading(self):
        self._win.addstr(self.__timer_heading_y,
                         self.__timer_heading_start_x,
                         self.__timer_heading,
                         curses.A_BOLD|self._colors.attr('text_default'))

    def __draw_timer(self):
        now = datetime.datetime.now()
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        midnight_tomorrow = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        total_seconds_until_midnight = (midnight_tomorrow - now).total_seconds()
        until_midnight_hours = int(total_seconds_until_midnight/3600)
        until_midnight_minutes = int((total_seconds_until_midnight-3600*until_midnight_hours)/60)
        until_midnight_seconds = int(total_seconds_until_midnight-3600*until_midnight_hours-60*until_midnight_minutes)
        until_midnight_str = (f'{until_midnight_hours:02}:'
                              f'{until_midnight_minutes:02}:'
                              f'{until_midnight_seconds:02}')
        until_midnight_lines = fancytext.bignum(until_midnight_str,
                                                fixed_width_numerals=True)
        for y_offset, line in enumerate(until_midnight_lines):
            self._win.addstr(self.__timer_start_y+y_offset,
                             self.__timer_start_x,
                             line,
                             self._colors.attr('text_default'))

    def __draw_timer_share_divider(self):
        self._win.addstr(self.__timer_share_divider_line_start_y,
                         self.__timer_share_divider_line_x,
                         self.__VERTICAL_SEPARATOR_TOP,
                         self._colors.attr('vertical_separator_line'))
        for y_offset in range(1, self.__timer_share_divider_line_height):
            self._win.addstr(self.__timer_share_divider_line_start_y+y_offset,
                             self.__timer_share_divider_line_x,
                             self.__VERTICAL_SEPARATOR,
                             self._colors.attr('vertical_separator_line'))

    def __draw_share_button(self):
        for y_offset in range(self.__share_button_height):
            self._win.addstr(self.__share_button_start_y+y_offset,
                             self.__share_button_start_x,
                             ' '*self.__share_button_width,
                             self._colors.attr('share_button'))
        self._win.addstr(self.__share_button_text_icon_y,
                         self.__share_button_text_start_x,
                         self.__share_button_text,
                         curses.A_BOLD|self._colors.attr('share_button'))
        self._win.addstr(self.__share_button_text_icon_y,
                         self.__share_button_icon_start_x,
                         glyphs.SHARE_ICON, # ⚬𝈶ⵓ
                         self._colors.attr('share_button_icon'))
        self._input.add_to_click_map(self.__share_button_start_y,
                                     self.__share_button_start_x,
                                     self.__share_button_height,
                                     self.__share_button_width,
                                     self.__share)

    def _run(self):

        # set background
        self._win.bkgd(self._colors.attr('background'))

        self.__draw_close_button()
        self.__draw_stats()
        self.__draw_guess_distribution()
        if self.__game_core.play_stats.any_completed() and self.__game_core.is_completed():
            self.__draw_timer_heading()
            self.__draw_timer()
            self.__draw_timer_share_divider()
            self.__draw_share_button()
        self._input.add_default_to_click_map(self.__close)

        # some init
        self.__closing = False

        # event loop
        if self.__game_core.play_stats.any_completed() and self.__game_core.is_completed():
            self._input.set_non_blocking(100, self.__draw_timer)
        while not self.__closing:
            k = self._input.get(self.__min_required_screen_height,
                                self.__min_required_screen_width)
            if k == 's' and self.__shareable_status is not None:
                toast = Toast(self._stdscr, self._colors)
                if self.__shareable_status.copy_to_clipboard():
                    toast.run('Copied shareable status to clipboard')
                else:
                    toast.run('Share failed')
            if k == '~': break

    def run(self,
            parent_min_required_total_height,
            parent_min_required_total_width):
        (panel_height, panel_width) = self.__init_size_calculations()
        (screen_rows, screen_cols) = self._stdscr.getmaxyx()

        self.__min_required_screen_height = max(panel_height, parent_min_required_total_height)
        self.__min_required_screen_width  = max(panel_width,  parent_min_required_total_width)

        if screen_rows < self.__min_required_screen_height or screen_cols < self.__min_required_screen_width:
            raise WindowResized(screen_rows,
                                screen_cols,
                                self.__min_required_screen_height,
                                self.__min_required_screen_width,
                                self.__class__.__name__)
        start_y = (screen_rows-panel_height)//2
        start_x = (screen_cols-panel_width)//2
        super().run(panel_height,
                    panel_width,
                    start_y,
                    start_x)
