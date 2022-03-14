# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

class ColorsChanged(Exception):
    def __init__(self, current_panel_name):
        self.aborted_panel_name = current_panel_name

class WindowResized(Exception):
    def __init__(self, height, width, min_height, min_width, current_panel_name):
        self.too_small          = height < min_height or width < min_width
        self.min_height         = min_height
        self.min_width          = min_width
        self.aborted_panel_name = current_panel_name
