# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import subprocess

import clipboard

from constants import GAME_NAME
from gamecore  import LetterStatus

class ShareableStatus:

    __STATUS_GLYPHS = {#status                        normal        dark          high cont.    dark high cont.
                       LetterStatus.WRONG.value:     ['\u2b1c',     '\u2b1b',     '\u2b1c',     '\u2b1b'],     # ⬜⬛⬜⬛
                       LetterStatus.MISPLACED.value: ['\U0001f7e8', '\U0001f7e8', '\U0001f7e6', '\U0001f7e6'], # 🟨🟨🟦🟦
                       LetterStatus.RIGHT.value:     ['\U0001f7e9', '\U0001f7e9', '\U0001f7e7', '\U0001f7e7']} # 🟩🟩🟧🟧

    def __init__(self, game_core, game_num_str, config):
        style_index = int(config.dark_mode)+2*int(config.high_contrast_mode)
        text_segments = [f'{GAME_NAME} {game_num_str} ']
        if game_core.is_won():
            text_segments.append(f'{len(game_core.guesses)}')
        elif game_core.is_lost():
            text_segments.append('X')
        else:
            text_segments.append('?')
        text_segments.append(f'/{game_core.MAX_GUESSES}')
        if config.hard_mode:
            text_segments.append('*')
        text_segments.append('\n')
        for guess in game_core.guesses:
            text_segments.append('\n')
            for s in guess['letter_statuses']:
                text_segments.append(self.__STATUS_GLYPHS[s.value][style_index])
        self.__text = ''.join(text_segments)

    def copy_to_clipboard(self):
        return clipboard.put(self.__text)
