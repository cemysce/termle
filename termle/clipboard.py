# Copyright (c) 2022, cemysce
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import subprocess

def put(text):
    # cannot use `xsel` with multiple selections at once or it will silently
    #  use only one of them
    all_succeeded = True
    for selection in ('primary', 'clipboard'):
        cp = subprocess.run(['xsel', '--input', f'--{selection}'],
                            input=text,
                            capture_output=True,
                            text=True)
        if cp.returncode != 0:
            all_succeeded = False
    return all_succeeded
