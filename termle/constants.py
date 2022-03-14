# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# NOTE: These are all tweakable, but have undocumented constraints that the
#        code may or may not check for.  Don't be surprised if certain values
#        result in errant behavior.
GAME_NAME            = 'Termle'
GAME_NAME_STYLIZED   = ('\u2576\u252c\u2574' ' \u256d\u2500\u2574' ' \u256d\u2500\u256e' ' \u256d\u252c\u256e' ' \u2577  '           ' \u256d\u2500\u2574', #╶┬╴ ╭─╴ ╭─╮ ╭┬╮ ╷   ╭─╴
                             ' \u2502 '      ' \u251c\u2574 '      ' \u251c\u252c\u256f' ' \u2502\u2575\u2502' ' \u2502  '           ' \u251c\u2574 ',      # │  ├╴  ├┬╯ │╵│ │   ├╴
                             ' \u2575 '      ' \u2570\u2500\u2574' ' \u2575\u2570\u2574' ' \u2575 '   '\u2575' ' \u2570\u2500\u2574' ' \u2570\u2500\u2574') # ╵  ╰─╴ ╵╰╴ ╵ ╵ ╰─╴ ╰─╴
CONFIG_FILENAME      = f'{GAME_NAME.lower()}-config.json'
DAILY_STATE_FILENAME = f'{GAME_NAME.lower()}-daily-state.json'
WORDS_FILENAME       = f'{GAME_NAME.lower()}-words.json'
