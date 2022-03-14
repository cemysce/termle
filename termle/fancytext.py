# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from copy      import deepcopy
from itertools import chain

# NOTE 1: Some characters below are disabled, even though they have a
#          superscript/subscript equivalent in Unicode, because they were
#          only recently added to Unicode, so they are supportd by few to
#          none of the fonts needed by the rest of this program.
# NOTE 2: Some characters below are disabled because they have no
#          superscript/subscript equivalent in Unicode.
# NOTE 3: Some character replacements aren't technically
#          superscript/subscript, but they seem to be aesthetically close
#          enough.
# NOTE 4: Some character replacements may be no-ops (replacement is same
#          as original), these are in the table so that the validation
#          logic won't consider consider them invalid.
# NOTE 5: Some character replacements are double-wide.
#
#                 normal  replacement   width   preview & notes
__SUPERSCRIPTS = {' ':   (         ' ',     1),       # see note 4 above
                  '+':   (    '\u207a',     1), #  ⁺  #
                  '-':   (    '\u207b',     1), #  ⁻  #
                  '/':   (    '\u141f',     1), #  ᐟ  #
                  '=':   (    '\u207c',     1), #  ⁼  #
                  '(':   (    '\u207d',     1), #  ⁽  #
                  ')':   (    '\u207e',     1), #  ⁾  #
                  '#':   (    '\u266f',     1), #  ♯  # see note 3 above
                  '%':   ('\U00010a50'
                              '\u141f'
                          '\U00010101',     3), # 𐩐ᐟ𐄁 #
                  ',':   (    '\u02d2',     1), #  ˒  #
                  '.':   ('\U00010101',     1), #  𐄁  #
                  '0':   (    '\u2070',     1), #  ⁰  #
                  '1':   (    '\u00b9',     1), #  ¹  #
                  '2':   (    '\u00b2',     1), #  ²  #
                  '3':   (    '\u00b3',     1), #  ³  #
                  '4':   (    '\u2074',     1), #  ⁴  #
                  '5':   (    '\u2075',     1), #  ⁵  #
                  '6':   (    '\u2076',     1), #  ⁶  #
                  '7':   (    '\u2077',     1), #  ⁷  #
                  '8':   (    '\u2078',     1), #  ⁸  #
                  '9':   (    '\u2079',     1), #  ⁹  #
                  'A':   (    '\u1d2c',     1), #  ᴬ  #
                  'B':   (    '\u1d2e',     1), #  ᴮ  #
                 #'C':   (    '\ua7f2',     1), #  ꟲ  # see note 1 above
                  'D':   (    '\u1d30',     1), #  ᴰ  #
                  'E':   (    '\u1d31',     1), #  ᴱ  #
                 #'F':   (    '\ua7f3',     1), #  ꟳ  # see note 1 above
                  'G':   (    '\u1d33',     1), #  ᴳ  #
                  'H':   (    '\u1d34',     1), #  ᴴ  #
                  'I':   (    '\u1d35',     1), #  ᴵ  #
                  'J':   (    '\u1d36',     1), #  ᴶ  #
                  'K':   (    '\u1d37',     1), #  ᴷ  #
                  'L':   (    '\u1d38',     1), #  ᴸ  #
                  'M':   (    '\u1d39',     1), #  ᴹ  #
                  'N':   (    '\u1d3a',     1), #  ᴺ  #
                  'O':   (    '\u1d3c',     1), #  ᴼ  #
                  'P':   (    '\u1d3e',     1), #  ᴾ  #
                 #'Q':   (    '\ua7f4',     1), #  ꟴ  # see note 1 above
                  'R':   (    '\u1d3f',     1), #  ᴿ  #
                 #'S':                ,               # see note 2 above
                  'T':   (    '\u1d40',     1), #  ᵀ  #
                  'U':   (    '\u1d41',     1), #  ᵁ  #
                  'V':   (    '\u2c7d',     1), #  ⱽ  #
                  'W':   (    '\u1d42',     1), #  ᵂ  #
                 #'X':                                # see note 2 above
                 #'Y':                                # see note 2 above
                 #'Z':                                # see note 2 above
                  'a':   (    '\u1d43',     1), #  ᵃ  #
                  'b':   (    '\u1d47',     1), #  ᵇ  #
                  'c':   (    '\u1d9c',     1), #  ᶜ  #
                  'd':   (    '\u1d48',     1), #  ᵈ  #
                  'e':   (    '\u1d49',     1), #  ᵉ  #
                  'f':   (    '\u1da0',     1), #  ᶠ  #
                  'g':   (    '\u1d4d',     1), #  ᵍ  #
                  'h':   (    '\u02b0',     1), #  ʰ  #
                  'i':   (    '\u2071',     1), #  ⁱ  #
                  'j':   (    '\u02b2',     1), #  ʲ  #
                  'k':   (    '\u1d4f',     1), #  ᵏ  #
                  'l':   (    '\u02e1',     1), #  ˡ  #
                  'm':   (    '\u1d50',     1), #  ᵐ  #
                  'n':   (    '\u207f',     1), #  ⁿ  #
                  'o':   (    '\u1d52',     1), #  ᵒ  #
                  'p':   (    '\u1d56',     1), #  ᵖ  #
                 #'q':   ('\U000107a5',     1), #  𐞥  # see note 1 above
                  'r':   (    '\u02b3',     1), #  ʳ  #
                  's':   (    '\u02e2',     1), #  ˢ  #
                  't':   (    '\u1d57',     1), #  ᵗ  #
                  'u':   (    '\u1d58',     1), #  ᵘ  #
                  'v':   (    '\u1d5b',     1), #  ᵛ  #
                  'w':   (    '\u02b7',     1), #  ʷ  #
                  'x':   (    '\u02e3',     1), #  ˣ  #
                  'y':   (    '\u02b8',     1), #  ʸ  #
                  'z':   (    '\u1dbb',     1)} #  ᶻ  #
__SUBSCRIPTS   = {' ':   (         ' ',     1),       # see note 4 above
                  '+':   (    '\u208a',     1), #  ₊  #
                  '-':   (    '\u208b',     1), #  ₋  #
                  '=':   (    '\u208c',     1), #  ₌  #
                  '(':   (    '\u208d',     1), #  ₍  #
                  ')':   (    '\u208e',     1), #  ₎  #
                  '#':   (    '\ufe5f',     2), #  ﹟ # see note 5 above
                  '%':   (    '\ufe6a',     2), #  ﹪ # see note 5 above
                  '0':   (    '\u2080',     1), #  ₀  #
                  '1':   (    '\u2081',     1), #  ₁  #
                  '2':   (    '\u2082',     1), #  ₂  #
                  '3':   (    '\u2083',     1), #  ₃  #
                  '4':   (    '\u2084',     1), #  ₄  #
                  '5':   (    '\u2085',     1), #  ₅  #
                  '6':   (    '\u2086',     1), #  ₆  #
                  '7':   (    '\u2087',     1), #  ₇  #
                  '8':   (    '\u2088',     1), #  ₈  #
                  '9':   (    '\u2089',     1)} #  ₉  #

def __maketrans_for_1to1(CHAR_INFOS):
    return str.maketrans({normal: replacement for normal, (replacement, width)
                                               in CHAR_INFOS.items()})

__SUPERSCRIPT_TRANSLATION_TABLE = __maketrans_for_1to1(__SUPERSCRIPTS)
__SUBSCRIPT_TRANSLATION_TABLE   = __maketrans_for_1to1(__SUBSCRIPTS)

def __1to1_convert(CHAR_INFOS,
                   TRANSLATION_TABLE,
                   s,
                   calc_width,
                   convert):
    if any(ord(c) not in TRANSLATION_TABLE for c in s):
        raise

    r = []
    if calc_width:
        r.append(sum(CHAR_INFOS[c][1] for c in s))
    if convert:
        r.append(s.translate(TRANSLATION_TABLE))

    if len(r) > 1:
        return tuple(r)
    if len(r) == 1:
        return r[0]

def superscript(s, *, calc_width=False, convert=True):
    return __1to1_convert(__SUPERSCRIPTS,
                          __SUPERSCRIPT_TRANSLATION_TABLE,
                          s,
                          calc_width,
                          convert)

def subscript(s, *, calc_width=False, convert=True):
    return __1to1_convert(__SUBSCRIPTS,
                          __SUBSCRIPT_TRANSLATION_TABLE,
                          s,
                          calc_width,
                          convert)

__BIGNUM_NUMERALS = [['\u256d\u2500\u256e',  # ╭─╮
                      '\u2502 '   '\u2502',  # │ │
                      '\u2570\u2500\u256f'], # ╰─╯
                     [     ' \u2510',        #  ┐
                           ' \u2502',        #  │
                           ' \u2575'      ], #  ╵
                     ['\u256d\u2500\u256e',  # ╭─╮
                      '\u256d\u2500\u256f',  # ╭─╯
                      '\u2514\u2500\u2574'], # └─╴
                     ['\u256d\u2500\u256e',  # ╭─╮
                           ' \u2576\u2524',  #  ╶┤
                      '\u2570\u2500\u256f'], # ╰─╯
                     ['\u2577 '   '\u2577',  # ╷ ╷
                      '\u2514\u2500\u253c',  # └─┼
                                '  \u2575'], #   ╵
                     ['\u250c\u2500\u2574',  # ┌─╴
                      '\u2514\u2500\u256e',  # └─╮
                      '\u2570\u2500\u256f'], # ╰─╯
                     ['\u256d\u2500\u256e',  # ╭─╮
                      '\u251c\u2500\u256e',  # ├─╮
                      '\u2570\u2500\u256f'], # ╰─╯
                     ['\u2576\u2500\u2510',  # ╶─┐
                           ' \u256d\u256f',  #  ╭╯
                           ' \u2575 '     ], #  ╵
                     ['\u256d\u2500\u256e',  # ╭─╮
                      '\u251c\u2500\u2524',  # ├─┤
                      '\u2570\u2500\u256f'], # ╰─╯
                     ['\u256d\u2500\u256e',  # ╭─╮
                      '\u2570\u2500\u2524',  # ╰─┤
                      '\u2570\u2500\u256f']] # ╰─╯
__BIGNUM_NUMERALS_FIXED_WIDTH = deepcopy(__BIGNUM_NUMERALS)
__BIGNUM_NUMERALS_FIXED_WIDTH[1] = [' \u2510 ',  #  ┐
                                    ' \u2502 ',  #  │
                                    ' \u2575 ' ] #  ╵
__BIGNUM_NUMERALS_NARROW = [['\u256d\u256e',  # ╭╮
                             '\u2502\u2502',  # ││
                             '\u2570\u256f'], # ╰╯
                            [      '\u2510',  #  ┐
                                   '\u2502',  #  │
                                   '\u2575'], #  ╵
                            ['\u256d\u256e',  # ╭╮
                             '\u256d\u256f',  # ╭╯
                             '\u2514\u2574'], # └╴
                            ['\u256d\u256e',  # ╭╮
                                  ' \u2524',  #  ┤
                             '\u2570\u256f'], # ╰╯
                            ['\u2577\u2577',  # ╷╷
                             '\u2514\u253c',  # └┼
                                  ' \u2575'], #  ╵
                            ['\u250c\u2574',  # ┌╴
                             '\u2514\u256e',  # └╮
                             '\u2570\u256f'], # ╰╯
                            ['\u256d\u256e',  # ╭╮
                             '\u251c\u256e',  # ├╮
                             '\u2570\u256f'], # ╰╯
                            ['\u2500\u2510',  # ─┐
                             '\u256d\u256f',  # ╭╯
                             '\u2575 '     ], # ╵
                            ['\u256d\u256e',  # ╭╮
                             '\u251c\u2524',  # ├┤
                             '\u2570\u256f'], # ╰╯
                            ['\u256d\u256e',  # ╭╮
                             '\u2570\u2524',  # ╰┤
                             '\u2570\u256f']] # ╰╯
__BIGNUM_NUMERALS_NARROW_FIXED_WIDTH = deepcopy(__BIGNUM_NUMERALS_NARROW)
__BIGNUM_NUMERALS_NARROW_FIXED_WIDTH[1] = [' \u2510',  #  ┐
                                           ' \u2502',  #  │
                                           ' \u2575' ] #  ╵
__BIGNUM_COLON = [' ',      #
                  '\u02d9', # ˙
                  '\u02d9'] # ˙
def __calc_glyphs_height(glyphs):
    unique_heights = {len(glyph_lines) for glyph_lines in glyphs}
    assert len(unique_heights)==1
    return unique_heights.pop()
def __calc_glyphs_max_width(glyphs):
    assert all(len({len(line) for line in glyph_lines})==1
               for glyph_lines in glyphs) # for each glyph, all lines have same width
    return max(len(line) for glyph_lines in glyphs for line in glyph_lines)
def __calc_glyphs_fixed_width(glyphs):
    assert len({len(line)
                for glyph_lines in glyphs
                for line in glyph_lines})==1 # all lines of all glyphs have same width
    return len(glyphs[0][0])
BIGNUM_HEIGHT                            = __calc_glyphs_height(chain(__BIGNUM_NUMERALS,
                                                                      __BIGNUM_NUMERALS_FIXED_WIDTH,
                                                                      __BIGNUM_NUMERALS_NARROW,
                                                                      __BIGNUM_NUMERALS_NARROW_FIXED_WIDTH,
                                                                      [__BIGNUM_COLON]))
BIGNUM_NUMERALS_MAX_WIDTH                = __calc_glyphs_max_width(__BIGNUM_NUMERALS)
BIGNUM_NUMERALS_NARROW_MAX_WIDTH         = __calc_glyphs_max_width(__BIGNUM_NUMERALS_NARROW)
BIGNUM_NUMERALS_FIXED_WIDTH_WIDTH        = __calc_glyphs_fixed_width(__BIGNUM_NUMERALS_FIXED_WIDTH)
BIGNUM_NUMERALS_NARROW_FIXED_WIDTH_WIDTH = __calc_glyphs_fixed_width(__BIGNUM_NUMERALS_NARROW_FIXED_WIDTH)
BIGNUM_COLON_WIDTH                       = __calc_glyphs_max_width([__BIGNUM_COLON])

def bignum(s, *, narrow=False, fixed_width_numerals=False, calc_width=False):
    if any(c not in [str(n) for n in range(10)]+[':'] for c in s):
        raise RuntimeError(s)
    if narrow:
        if fixed_width_numerals:
            numeral_glyphs = __BIGNUM_NUMERALS_NARROW_FIXED_WIDTH
            max_width      = BIGNUM_NUMERALS_NARROW_FIXED_WIDTH_WIDTH
        else:
            numeral_glyphs = __BIGNUM_NUMERALS_NARROW
            max_width      = BIGNUM_NUMERALS_NARROW_MAX_WIDTH
    else:
        if fixed_width_numerals:
            numeral_glyphs = __BIGNUM_NUMERALS_FIXED_WIDTH
            max_width      = BIGNUM_NUMERALS_FIXED_WIDTH_WIDTH
        else:
            numeral_glyphs = __BIGNUM_NUMERALS
            max_width      = BIGNUM_NUMERALS_MAX_WIDTH
    lines = []
    for y in range(BIGNUM_HEIGHT):
        glyph_segments = []
        for c in s:
            if c == ':':
                glyph_segments += __BIGNUM_COLON[y]
            else:
                glyph_line = numeral_glyphs[int(c)][y]
                glyph_segments += glyph_line
        lines.append(''.join(glyph_segments))
    if calc_width:
        return (len(lines[0]), lines) # it's safe to just check first line, because of all the assertions above
    return lines
