# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from ..modalpanel import ModalPanel

class HelpPanel(ModalPanel):

    def __init__(self, stdscr, colors):
        super().__init__(stdscr, colors)
        self.__closing = None

    def __close(self):
        self.__closing = True

    def _run(self,
             parent_min_required_total_height,
             parent_min_required_total_width):

        # set background
        self._win.bkgd(self._colors.attr('background'))

        self._input.add_default_to_click_map(self.__close)

        # some init
        self.__closing = False

        # event loop
        while not self.__closing:
            # NOTE: Using parent panel's size constraints as this panel's.
            k = self._input.get(parent_min_required_total_height,
                                parent_min_required_total_width)
            if k == '~': break
