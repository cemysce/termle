#!/usr/bin/env python3.8

# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import sys

import constants

from arguments         import Arguments
from configuration     import Configuration
from gamecore          import GameCore
from graphics.graphics import Graphics
from savedstate        import DailyStateManager
from words             import Words

def main():
    args = Arguments()
    if args.download:
        word_lists = Words(constants.WORDS_FILENAME, True)
    else:
        word_lists = Words(constants.WORDS_FILENAME)
        if args.deobfuscate or args.deobfuscate_with_spoilers:
            if args.deobfuscate:
                print('Sorted answers:')
                for a in sorted(word_lists.all_answers()):
                    print(a)
                print('Additional valid guesses:')
                print('\n'.join(word_lists.additional_valid_guesses()))
            elif args.deobfuscate_with_spoilers:
                print('Daily answers:')
                for i,a in enumerate(word_lists.all_answers()):
                    print(f'#{i}: {a}')
                print('Additional valid guesses:')
                print('\n'.join(word_lists.additional_valid_guesses()))
            else:
                assert False
            pass
        elif args.word_stats:
            word_lists.print_statistics()
        else:
            config = Configuration(constants.CONFIG_FILENAME)
            if args.play_daily:
                (day_offset,
                 is_for_today,
                 answer) = word_lists.daily_answer(args.play_daily)
                if any(x is None for x in (day_offset, is_for_today, answer)):
                    raise
                if is_for_today:
                    daily_state_manager = DailyStateManager(constants.DAILY_STATE_FILENAME,
                                                            word_lists.hash_digest(),
                                                            config.max_guesses,
                                                            day_offset)
                    (saved_play_stats,
                     saved_guesses,
                     saved_pending_guess_letters) = daily_state_manager.get()
                    game_core = GameCore(answer,
                                         word_lists.valid_guesses(),
                                         config.max_guesses,
                                         config.hard_mode,
                                         saved_play_stats,
                                         saved_guesses,
                                         saved_pending_guess_letters)
                else:
                    game_core = GameCore(answer,
                                         word_lists.valid_guesses(),
                                         config.max_guesses,
                                         config.hard_mode)
            else:
                game_core = GameCore(word_lists.random_answer(),
                                     word_lists.valid_guesses(),
                                     config.max_guesses,
                                     config.hard_mode)

            if args.play_daily:
                gui = Graphics(game_core, config, str(day_offset))
            else:
                gui = Graphics(game_core, config)
            gui.run()

            if args.play_daily and is_for_today:
                daily_state_manager.save(game_core.play_stats,
                                         [guess['word']
                                          for guess in game_core.guesses],
                                         game_core.pending_guess_letters[:], # shallow copy the list (each element is immutable so no need to deep copy)
                                         game_core.is_completed())
            config.save()

if __name__ == '__main__':
    sys.exit(main())
