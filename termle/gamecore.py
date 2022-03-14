# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import enum
import itertools

from collections import Counter

class LetterStatus(enum.Enum):
    # This is deliberately defined in order from most right to most wrong,
    #  because Enum classes can be iterated over (i.e. `for x in LetterStatus`)
    #  and there's code that depends on the iteration being in that order.
    RIGHT     = 'right'
    MISPLACED = 'misplaced'
    WRONG     = 'wrong'

class GuessResult(enum.Enum):
    RIGHT                                                 = 'right_guess'
    WRONG_AND_GAME_OVER                                   = 'wrong_guess_game_over'
    WRONG                                                 = 'wrong_guess'
    INVALID_HARD_MODE_MISSING_PREV_GUESS_CORRECT_LETTER   = 'invalid_hard_missing_correct'
    INVALID_HARD_MODE_MISSING_PREV_GUESS_MISPLACED_LETTER = 'invalid_hard_missing_misplaced'
    INVALID                                               = 'invalid'
    INVALID_TOO_SHORT                                     = 'invalid_short'

class GameCore:

    def __init__(self,
                 answer,
                 valid_guesses,
                 max_guesses,
                 hard_mode,
                 play_stats=None,
                 init_guesses=[],
                 init_pending_guess_letters=[]):

        # calculate word length
        word_length = len(answer)

        # assert that word length meets minimum requirement
        assert word_length > 0

        # assert that all characters are alphabetic
        #  and that all words have same length as answer
        #  and that each pending guess letter is exactly 1 character
        assert answer.isalpha()
        assert all(guess.isalpha() and len(guess) == word_length
                   for guess in itertools.chain(valid_guesses,
                                                init_guesses))
        assert all(l.isalpha() and len(l) == 1
                   for l in init_pending_guess_letters)

        # assert that max guesses is at least 1 and that any initial guess
        #  state (guesses made, pending guess letters) fits within that limit
        assert max_guesses > 0
        assert (   len(init_guesses) + (1 if init_pending_guess_letters else 0)
                <= max_guesses)

        # normalize all characters to lowercase
        answer_lower = answer.lower()
        valid_guesses_lower = {valid_guess.lower()
                               for valid_guess in valid_guesses}
        init_guesses_lower = [init_guess.lower()
                              for init_guess in init_guesses]
        init_pending_guess_letters_lower = [l.lower()
                                            for l in init_pending_guess_letters]

        # assert that answer is within list of valid guesses
        #  and is not among any of initial guesses (other than last guess)
        assert answer_lower in valid_guesses_lower
        assert answer_lower not in init_guesses[:-1]

        # game parameters
        self.__ANSWER        = answer_lower
        self.__VALID_GUESSES = valid_guesses_lower
        self.WORD_LENGTH     = word_length
        self.MAX_GUESSES     = max_guesses
        self.HARD_MODE       = hard_mode

        # game state
        self.play_stats            = play_stats
        self.guesses               = []
        self.pending_guess_letters = init_pending_guess_letters_lower
        for guess_word in init_guesses_lower:
            self.__ingest_guess(guess_word)

    def change_max_guesses(self, max_guesses):
        if max_guesses < len(self.guesses)+1:
            return False
        self.MAX_GUESSES = max_guesses
        return True

    def toggle_hard_mode(self, hard_mode=None):
        if hard_mode is None:
            hard_mode = not self.HARD_MODE
        if hard_mode and self.in_progress():
            # not permitted to enable hard mode if game already in progress
            return False
        self.HARD_MODE = hard_mode
        return True

    def letter_status(self, l):
        l = l.lower()
        statuses = {guess['letter_statuses'][i]
                    for guess in self.guesses
                    for i in range(self.WORD_LENGTH)
                    if guess['word'][i]==l}
        for s in LetterStatus:
            if s in statuses:
                return s
        return None

    def is_started(self):
        return len(self.guesses)>0

    def is_won(self):
        return (    len(self.guesses) > 0
                and all(s == LetterStatus.RIGHT
                        for s in self.guesses[-1]['letter_statuses']))

    def is_lost(self):
        return len(self.guesses) == self.MAX_GUESSES and not self.is_won()

    def is_completed(self):
        return len(self.guesses) == self.MAX_GUESSES or self.is_won()

    def in_progress(self):
        return self.is_started() and not self.is_completed()

    def append_letter_to_pending_guess(self, l):
        if (   self.is_completed()
            or len(l) != 1
            or not l.isalpha()
            or len(self.pending_guess_letters) == self.WORD_LENGTH):
            return False
        self.pending_guess_letters.append(l.lower())
        return True

    def remove_last_letter_from_pending_guess(self):
        if len(self.pending_guess_letters) == 0:
            return False
        self.pending_guess_letters.pop()
        return True

    def __ingest_guess(self, guess_word):
        latest_guess_correct_letters = [(guess_word[i]
                                         if guess_word[i] == self.__ANSWER[i] else
                                         None)
                                        for i in range(self.WORD_LENGTH)]
        latest_guess_misplaced_letter_counts = Counter()
        guess_letter_statuses = self.WORD_LENGTH*[None]
        for i in range(self.WORD_LENGTH):
            if guess_word[i] == self.__ANSWER[i]:
                guess_letter_statuses[i] = LetterStatus.RIGHT
            elif self.__ANSWER.count(guess_word[i]) > (  latest_guess_misplaced_letter_counts[guess_word[i]]
                                                       + latest_guess_correct_letters.count(guess_word[i])):
                guess_letter_statuses[i] = LetterStatus.MISPLACED
                latest_guess_misplaced_letter_counts[guess_word[i]]+=1
            else:
                guess_letter_statuses[i] = LetterStatus.WRONG
        self.guesses.append({'word':            guess_word,
                             'letter_statuses': guess_letter_statuses})

    def answer(self):
        if self.is_completed():
            return self.__ANSWER
        return None

    def submit_pending_guess(self):
        guess_word = ''.join(self.pending_guess_letters)

        # check for cases of invalidity
        if len(guess_word) < self.WORD_LENGTH:
            return (GuessResult.INVALID_TOO_SHORT, None, None)
        if guess_word not in self.__VALID_GUESSES:
            return (GuessResult.INVALID, None, None)
        if self.HARD_MODE and len(self.guesses)>0:
            # first check if any previous correct letters are not in same spot in new guess:
            for i,(l,s) in enumerate(zip(self.guesses[-1]['word'],
                                         self.guesses[-1]['letter_statuses'])):
                if s == LetterStatus.RIGHT and guess_word[i] != l:
                    return (GuessResult.INVALID_HARD_MODE_MISSING_PREV_GUESS_CORRECT_LETTER,
                            l,
                            i)
            # *then* check if any previous misplaced letters are not in new guess:
            #  (yes it's the same loop parameters as above, but we need to
            #   prefer the missing correct letter status over the missing
            #   misplaced letter status)
            for i,(l,s) in enumerate(zip(self.guesses[-1]['word'],
                                         self.guesses[-1]['letter_statuses'])):
                if s == LetterStatus.MISPLACED and l not in guess_word:
                    return (GuessResult.INVALID_HARD_MODE_MISSING_PREV_GUESS_MISPLACED_LETTER,
                            l,
                            None)

        # update internal state
        self.pending_guess_letters.clear()
        self.__ingest_guess(guess_word)

        # return valid guess result
        if self.is_won():
            if self.play_stats is not None:
                self.play_stats.register_win(len(self.guesses))
            return (GuessResult.RIGHT, None, None)
        if len(self.guesses) < self.MAX_GUESSES:
            return (GuessResult.WRONG, None, None)
        if self.play_stats is not None:
            self.play_stats.register_loss()
        return (GuessResult.WRONG_AND_GAME_OVER, None, None)
