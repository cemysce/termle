# Termle

A ~~blatant ripoff~~ loving attempt to faithfully recreate [Wordle](https://www.powerlanguage.co.uk/wordle/)'s gameplay **and** aesthetic... from a terminal.

## Requirements

This will be formalized eventually, but for now, know that the following are required:

* 256-color terminal with mouse support
* ncurses
* DejaVu Mono Book font (and terminal configured to use it)
* Python 3.8 or higher (if higher, for now you'll need to edit the `#!` in `termle.py`)

Also the following are recommended:

* `xsel` command for Share support
* [Python Requests module](https://docs.python-requests.org/en/latest/) needed to download word lists, which is required if you don't already them saved to disk

## Usage

Clone the repo and make sure you meet the requirements.  Discover the run options available.

```bash
git clone https://github.com/cemysce/termle.git
cd termle/termle
./termle.py --help
```

## Status

Supports all core features of upstream game:

* same word lists
* same daily word
* same gameplay rules
* same colors
* same configuration options
* same statistics tracked
* timer until next day
* sharing results using clipboard

Also supports:

* downloading word lists from upstream
* random play (won't track statistics)

Missing support for:

* Help panel/popup
* detecting and handling insufficient terminal support for 256 colors, mouse, etc.

There are numerous minor issues, and superficial differences from upstream game that are known and are being tracked.

---

Credit for the gameplay logic and visual design belongs to [Josh Wardle](https://www.powerlanguage.co.uk/),
but any ingenuity in recreating that visual design using only text belongs to me
_(okay, also the Unicode Consortium and the long history of box-drawing characters, without which this program would look nowhere near as good)_.

The logic for computing the daily game number (and the daily solution) was reproduced by inspecting upstream Wordle's JavaScript code.
Everything else was written by myself from scratch, to replicate the gameplay logic as I understood it from playing the game.
