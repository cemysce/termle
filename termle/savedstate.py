# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import os

from collections import defaultdict

from playstats import PlayStats

class DailyStateManager:

    def __init__(self,
                 file_path,
                 word_lists_hash_digest,
                 max_guesses,
                 day_offset):

        self.__FILE_PATH      = file_path
        self.__MAX_GUESSES    = max_guesses
        self.__STATE_KEY      = (f'wldig:{word_lists_hash_digest}'
                                 f'_maxg:{self.__MAX_GUESSES}')
        self.__PLAY_STATS_KEY = 'play_stats'
        self.__DAY_KEY        = f'day:{day_offset}'
        self.__PREV_DAY_KEY   = f'day:{day_offset-1}'

    def get(self):

        # return default initial state if no saved state file
        if (not os.path.exists(self.__FILE_PATH)):
            return (PlayStats(self.__MAX_GUESSES), [], [])

        # read saved state file
        with open(self.__FILE_PATH, 'r') as f:
            all_data = json.load(f)

        # return default initial state if no state corresponding to word lists
        if self.__STATE_KEY not in all_data:
            return (PlayStats(self.__MAX_GUESSES), [], [])

        data_for_specified_state_key = all_data[self.__STATE_KEY]
        if self.__PLAY_STATS_KEY not in data_for_specified_state_key:
            raise
        play_stats = PlayStats(self.__MAX_GUESSES)
        play_stats.load_from_json_dict(data_for_specified_state_key[self.__PLAY_STATS_KEY])

        data_for_specified_state_and_day_keys = None
        today_completed = False
        yesterday_completed = False
        if self.__DAY_KEY in data_for_specified_state_key:
            data_for_specified_state_and_day_keys = data_for_specified_state_key[self.__DAY_KEY]
            today_completed = data_for_specified_state_and_day_keys['is_completed']
        if self.__PREV_DAY_KEY in data_for_specified_state_key:
            yesterday_completed = data_for_specified_state_key[self.__PREV_DAY_KEY]['is_completed']
        if not today_completed and not yesterday_completed:
            play_stats.register_streak_lapse()

        if data_for_specified_state_and_day_keys is None:
            return (play_stats, [], [])
        return (play_stats,
                data_for_specified_state_and_day_keys['guesses'],
                data_for_specified_state_and_day_keys['pending_guess_letters'])

    def save(self, play_stats, guesses, pending_guess_letters, is_completed):
        if is_completed and (len(guesses)==0 or len(pending_guess_letters)>0):
            raise
        already_existed = os.path.exists(self.__FILE_PATH)
        with open(self.__FILE_PATH, 'r+' if already_existed else 'w') as f:
            all_data = defaultdict(dict)
            if already_existed:
                all_data.update(json.load(f))
                f.seek(0)
            all_data[self.__STATE_KEY][self.__PLAY_STATS_KEY] = play_stats.as_json_dict()
            all_data[self.__STATE_KEY][self.__DAY_KEY] = {'guesses':               guesses,
                                                          'pending_guess_letters': pending_guess_letters,
                                                          'is_completed':          is_completed}
            json.dump(all_data, f, indent=4, sort_keys=True)
            if already_existed:
                f.truncate()
