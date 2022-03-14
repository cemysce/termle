# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import textwrap
import sys

from constants import GAME_NAME, WORDS_FILENAME
from version   import __version__
from words     import _UPSTREAM_GAME_URL

class Arguments:

    PLAY_DAILY_TODAY = True

    class __HelpFormatter(argparse.RawDescriptionHelpFormatter):
        def add_usage(self, usage, actions, groups, prefix=None):
            if prefix is None:
                prefix = 'Usage: '
            return super().add_usage(usage, actions, groups, prefix)
        def _split_lines(self, text, width):
            # retain newlines in original text, while also wrapping each line
            #  (textwrap.wrap() is what removes newlines from text, so instead
            #   of calling it on entire text, we do text.splitlines() first and
            #   then textwrap.wrap() on each line individually)
            return [wrapped_line
                    for line in text.splitlines()
                    for wrapped_line in (textwrap.wrap(line, width)
                                         if line else
                                         [''])]

    @classmethod
    def __make_parser(cls):
        em_dash = '\u2014' # —
        parser = argparse.ArgumentParser(description=f'{GAME_NAME} {em_dash}'
                                                      ' A faithful recreation'
                                                      ' of a certain popular'
                                                      ' word guessing game,'
                                                      ' in a terminal.',

                                         # argparse's default -h/--help option
                                         #  is described in lowercase, which is
                                         #  inconsistent with other text, so we
                                         #  disable it here then explicitly add
                                         #  it ourselves the way we want it
                                         add_help=False,

                                         # argparse's default behavior is to
                                         #  accept unambiguously truncated
                                         #  command-line options, but often
                                         #  this is confusing, so require
                                         #  options exactly as they're defined
                                         allow_abbrev=False,

                                         # argparse's default prefix is in
                                         #  lowercase ("usage:"), which is
                                         #  inconsistent with other text, so we
                                         #  override it with a custom formatter
                                         # argparse removes extraneous newlines
                                         #  and whitespace from help text,
                                         #  which prevents complex display of
                                         #  information, so we override that
                                         #  logic in a custom formatter
                                         formatter_class=cls.__HelpFormatter)

        # argparse's default section headings for these are lowercase, which is
        #  inconsistent with other text
        parser._positionals.title = 'Positional Arguments'
        parser._optionals.title   = 'Optional Arguments'

        # add arguments
        parser.add_argument('-h', '--help',        action='help',              help= 'Print this usage information, then exit.')
        parser.add_argument('-V', '--version',     action='store_true',        help= 'Print version, then exit.')
        group = parser.add_mutually_exclusive_group()
        group.add_argument( '-D', '--download',    action='store_true',        help=f'Download word lists from {_UPSTREAM_GAME_URL} to'
                                                                                    f' "{WORDS_FILENAME}" (obfuscated so that you cannot'
                                                                                     ' accidentally spoil answers if you open it),'
                                                                                     ' overwriting any existing file with that name.')
        group.add_argument(       '--deobfuscate', action='store_true',        help=argparse.SUPPRESS) # Print deobfuscation of stored word lists,
                                                                                                       #  but sorted so that you cannot accidentally
                                                                                                       #  accidentally spoil specific daily answers.
        group.add_argument(       '--deobfuscate-with-spoilers',
                                                   action='store_true',        help=argparse.SUPPRESS) # THIS WILL SPOIL DAILY ANSWERS!  Does the
                                                                                                       #  same thing as --deobfuscate, but does not
                                                                                                       #  sort answer list before printing.
        group.add_argument(       '--word-stats',  action='store_true',        help=argparse.SUPPRESS) # Print some rudimentary statistical analysis
                                                                                                       #  of words in stored answer list.
        group.add_argument( '-d', '--play-daily',  metavar='DAY',
                                                   nargs='?',
                                                   default=False,
                                                   const=cls.PLAY_DAILY_TODAY, help= 'Play daily version of game.  Each day has a new answer.  Optionally specify which day\'s game to play.')

        return parser

    def __init__(self):
        self.__args = self.__make_parser().parse_args()
        if self.__args.version:
            print(f'{GAME_NAME} {__version__}')
            sys.exit()

    def __getattr__(self, name):
        return self.__args.__getattribute__(name)
