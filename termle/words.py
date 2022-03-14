# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import base64
import datetime
import hashlib
import itertools
import json
import os
import random
import re
import requests
import signal
import sys

from collections import Counter

#_UPSTREAM_GAME_URL = 'https://www.powerlanguage.co.uk/wordle' :'(
_UPSTREAM_GAME_URL = 'https://www.nytimes.com/games/wordle'

class Words:

    __FIRST_DAY = datetime.date(2021, 6, 19)

    __OBFUSCATIONS = {'Base16':  {'encode': base64.b16encode, 'decode': base64.b16decode},
                      'Base32':  {'encode': base64.b32encode, 'decode': base64.b32decode},
                      'Base64':  {'encode': base64.b64encode, 'decode': base64.b64decode},
                      'Base85':  {'encode': base64.b85encode, 'decode': base64.b85decode},
                      'Ascii85': {'encode': base64.a85encode, 'decode': base64.a85decode}}
    __DEFAULT_OBFUSCATION = 'Ascii85'

    @classmethod
    def __calc_day_offset(cls, date=datetime.date.today()):
        return (date - cls.__FIRST_DAY).days

    @classmethod
    def __obfuscate(cls, word_list, codec):
        return [cls.__OBFUSCATIONS[codec]['encode'](w.encode()).decode()
                for w in word_list]

    @classmethod
    def __deobfuscate(cls, obfuscated_word_list, codec):
        return [cls.__OBFUSCATIONS[codec]['decode'](ow.encode()).decode()
                for ow in obfuscated_word_list]

    def __init__(self, file_path, force_download=False):
        self.__answer_series            = []
        self.__additional_valid_guesses = set()
        self.__word_length              = None
        if force_download or not os.path.exists(file_path):
            self.__download_lists_and_write_file(file_path)
        else:
            self.__read_file(file_path)

    def __read_file(self, file_path):
        with open(file_path, 'r') as f:
            words = json.load(f)
        if not all(list_name in words for list_name in ('answer_series', 'additional_valid_guesses')):
            raise
        if 'obfuscation' in words:
            if words['obfuscation'] not in self.__OBFUSCATIONS:
                raise
            for list_name in ('answer_series', 'additional_valid_guesses'):
                words[list_name] = self.__deobfuscate(words[list_name], words['obfuscation'])
        lengths = {len(w)
                   for w in itertools.chain(words['answer_series'],
                                            words['additional_valid_guesses'])}
        if len(lengths) > 1:
            raise
        self.__answer_series            =     words['answer_series']
        self.__additional_valid_guesses = set(words['additional_valid_guesses'])
        self.__word_length              = lengths.pop()

    def __download_lists_and_write_file(self, file_path):
        def get_text_or_abort(url):
            rs = requests.get(url)
            if not rs.ok:
                print(f'Failed to get URL "{url}", with status {rs.status_code}!',
                      file=sys.stderr)
                return None
            return rs.text

        # download page to discover URL for JavaScript file
        html = get_text_or_abort(_UPSTREAM_GAME_URL)
        if not html:
            raise
        matches = re.findall(r'<script src="(main\.[0-9a-f]+\.js)">', html)
        if len(matches) != 1:
            print('Failed to determine URL for JavaScript source!',
                  file=sys.stderr)
            raise

        # download JavaScript file to discover word lists
        EXPECTED_WORD_LENGTH = 5
        js_url = f'{_UPSTREAM_GAME_URL}/{matches[0]}'
        js = get_text_or_abort(js_url)
        word_lists = [[word.strip('"') for word in word_list.split(',')]
                      for word_list in re.findall( r'=\[("[a-z]{'
                                                  +str(EXPECTED_WORD_LENGTH)
                                                  +r'}"(?:,"[a-z]{'
                                                  +str(EXPECTED_WORD_LENGTH)
                                                  +r'}")*)\]',
                                                  js)]
        if len(word_lists) != 2:
            print('Failed to locate word lists within JavaScript source!',
                  file=sys.stderr)
            raise
        if len(word_lists[0]) == len(word_lists[1]):
            print('Both word lists are same size, cannot tell them apart!',
                  file=sys.stderr)
            raise

        # determine which word list is which, then load them
        if len(word_lists[0]) < len(word_lists[1]):
            self.__answer_series            =     word_lists[0]
            self.__additional_valid_guesses = set(word_lists[1])
        elif len(word_lists[0]) > len(word_lists[1]):
            self.__answer_series            =     word_lists[1]
            self.__additional_valid_guesses = set(word_lists[0])
        else:
            assert False
        self.__word_length = EXPECTED_WORD_LENGTH

        # obfuscate word lists before writing them
        obfuscation = self.__DEFAULT_OBFUSCATION
        obfuscated_answer_series            = self.__obfuscate(self.__answer_series,
                                                               obfuscation)
        obfuscated_additional_valid_guesses = self.__obfuscate(sorted(self.__additional_valid_guesses),
                                                               obfuscation)

        # write obfuscated word lists to file
        with open(file_path, 'w') as f:
            json.dump({'source':                   js_url,
                       'answer_series':            obfuscated_answer_series,
                       'additional_valid_guesses': obfuscated_additional_valid_guesses,
                       'obfuscation':              obfuscation},
                      f,
                      indent=4)

    def print_statistics(self):
        overall_total_num_letters = len(self.__answer_series) * self.__word_length
        overall_letter_count_print_width = len(str(overall_total_num_letters))
        print(f'Overall Statistics:')
        for letter_count in Counter(itertools.chain(*self.__answer_series)).most_common():
            print(f'{letter_count[1]:{overall_letter_count_print_width}}/{overall_total_num_letters} {letter_count[0]}')
        per_letter_total_num_letters = len(self.__answer_series)
        per_letter_count_print_width = len(str(len(self.__answer_series)))
        for i in range(self.__word_length):
            print(f'\nLetter {i+1} Statistics:')
            for letter_count in Counter(a[i] for a in self.__answer_series).most_common():
                print(f'{letter_count[1]:{per_letter_count_print_width}}/{per_letter_total_num_letters} {letter_count[0]}')

    def daily_answer(self, day_spec=True):
        FAILURE = (None, None, None)
        day_offset_for_today = self.__calc_day_offset()
        if day_offset_for_today < 0:
            return FAILURE
        if type(day_spec) is str:
            if day_spec.isdecimal():
                day_offset = int(day_spec)
                if day_offset > day_offset_for_today:
                    return FAILURE
            else:
                day_parts = day_spec.split('-', 2) # 2 splits (3 parts) at most
                if len(day_parts) != 3 or any(not part.isdecimal() for part in day_parts):
                    return FAILURE
                day_parts = [int(part) for part in day_parts]
                date = datetime.date(year=day_parts[0],
                                     month=day_parts[1],
                                     day=day_parts[2])
                day_offset = self.__calc_day_offset(date)
                if day_offset < 0:
                    return FAILURE
                if day_offset > day_offset_for_today:
                    return FAILURE
        elif day_spec:
            day_offset = day_offset_for_today
        else:
            return FAILURE
        return (day_offset,
                day_offset==day_offset_for_today,
                self.__answer_series[day_offset % len(self.__answer_series)])

    def random_answer(self):
        return random.choice(self.__answer_series)

    def valid_guesses(self):
        return set(self.__answer_series) | self.__additional_valid_guesses

    def all_answers(self):
        return list(self.__answer_series)

    def additional_valid_guesses(self):
        return sorted(self.__additional_valid_guesses)

    def hash_digest(self):
        h = hashlib.sha256()

        # The strings chosen here are arbitrary, all that is important is that
        #  they be distinct from each other, and that they not be alphabetic
        #  (so that they can be distinct from the words):
        ANSWER_SERIES_HEADER            = b'*'
        ADDITIONAL_VALID_GUESSES_HEADER = b'?'
        WORD_DELIMITER                  = b':'

        h.update(ANSWER_SERIES_HEADER)
        for a in self.__answer_series:
            h.update(WORD_DELIMITER+a.encode())

        h.update(ADDITIONAL_VALID_GUESSES_HEADER)
        for g in sorted(self.__additional_valid_guesses):
            h.update(WORD_DELIMITER+g.encode())

        return h.hexdigest()
