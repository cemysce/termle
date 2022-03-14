# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import curses.panel

def back_to_front():
    p = curses.panel.bottom_panel()
    while p is not None:
        yield p
        p = p.above()

def front_to_back():
    p = curses.panel.top_panel()
    while p is not None:
        yield p
        p = p.below()
