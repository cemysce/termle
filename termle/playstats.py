# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from math import floor

class PlayStats:

    def __init__(self, max_guesses):
        self.__num_completed      = 0
        self.__num_won            = 0
        self.__current_streak     = 0
        self.__max_streak         = 0
        self.__guess_distribution = {g: 0 for g in range(1, max_guesses+1)}

    def any_completed(self):
        return self.__num_completed > 0

    def num_completed(self):
        return self.__num_completed

    def num_won(self):
        return self.__num_won

    def percent_won(self):
        if self.__num_completed == 0:
            return 0
        return floor(self.__num_won*100 / self.__num_completed)

    def current_streak(self):
        return self.__current_streak

    def max_streak(self):
        return self.__max_streak

    def guess_distribution(self):
        return self.__guess_distribution.copy()

    def register_win(self, num_guesses):
        if num_guesses < 1:
            raise
        self.__num_completed                   += 1
        self.__num_won                         += 1
        self.__current_streak                  += 1
        self.__max_streak                       = max(self.__max_streak,
                                                      self.__current_streak)
        self.__guess_distribution[num_guesses] += 1

    def register_loss(self):
        self.__num_completed += 1
        self.__current_streak = 0

    def register_streak_lapse(self):
        self.__current_streak = 0

    def load_from_json_dict(self, d):
        self.__num_completed  = d['num_completed']
        self.__num_won        = d['num_won']
        self.__current_streak = d['current_streak']
        self.__max_streak     = d['max_streak']

        # JSON requires field names to be strings, so conversion to JSON would
        #  have automatically converted the integer keys in this dict into
        #  strings, therefore we must convert them back.
        self.__guess_distribution = {int(k): v
                                     for k,v
                                      in d['guess_distribution'].items()}

    def as_json_dict(self):
        return {'num_completed':      self.__num_completed,
                'num_won':            self.__num_won,
                'current_streak':     self.__current_streak,
                'max_streak':         self.__max_streak,
                'guess_distribution': self.__guess_distribution}
