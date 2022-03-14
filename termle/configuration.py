# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import os

class Configuration:

    __DEFAULT_MAX_GUESSES        = 6
    __DEFAULT_HARD_MODE          = False
    __DEFAULT_DARK_MODE          = False
    __DEFAULT_HIGH_CONTRAST_MODE = False

    def __init__(self, file_path):

        self.__FILE_PATH = file_path

        self.max_guesses        = None
        self.hard_mode          = None
        self.dark_mode          = None
        self.high_contrast_mode = None

        if os.path.exists(self.__FILE_PATH):
            self.__read_file()
        else:
            self.max_guesses        = self.__DEFAULT_MAX_GUESSES
            self.hard_mode          = self.__DEFAULT_HARD_MODE
            self.dark_mode          = self.__DEFAULT_DARK_MODE
            self.high_contrast_mode = self.__DEFAULT_HIGH_CONTRAST_MODE

    def __read_file(self):
        with open(self.__FILE_PATH, 'r') as f:
            config = json.load(f)
        self.max_guesses        = config['max_guesses']        if 'max_guesses'        in config else self.__DEFAULT_MAX_GUESSES
        self.hard_mode          = config['hard_mode']          if 'hard_mode'          in config else self.__DEFAULT_HARD_MODE
        self.dark_mode          = config['dark_mode']          if 'dark_mode'          in config else self.__DEFAULT_DARK_MODE
        self.high_contrast_mode = config['high_contrast_mode'] if 'high_contrast_mode' in config else self.__DEFAULT_HIGH_CONTRAST_MODE

    def save(self):
        with open(self.__FILE_PATH, 'w') as f:
            json.dump({'max_guesses':        self.max_guesses,
                       'hard_mode':          self.hard_mode,
                       'dark_mode':          self.dark_mode,
                       'high_contrast_mode': self.high_contrast_mode},
                      f,
                      indent=4)
