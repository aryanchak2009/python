# Piano Simulator

A full 88-key piano (A0 - C8) you can play with your mouse or your computer
keyboard, built with `pygame`. Every note is synthesized on startup from a
few stacked harmonics with a plucked-string decay envelope — there are no
sample files, so it works offline right out of the box.

## Run it locally

1. Make sure you have Python 3.9+ installed.
2. From this folder, install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch it:

   ```bash
   python piano_simulator.py
   ```

A window should open showing the full keyboard. The first launch takes a
second or two while all 88 notes are synthesized.

## Controls

| Action                          | Keys                              |
|----------------------------------|------------------------------------|
| Play any key                     | Click (or click-and-drag) it with the mouse |
| Lower active-octave white keys   | `Z X C V B N M ,`                  |
| Lower active-octave black keys   | `S D` &nbsp; `G H J`               |
| Upper active-octave white keys   | `Q W E R T Y U I`                  |
| Upper active-octave black keys   | `2 3` &nbsp; `5 6 7`                |
| Shift keyboard octave down / up  | `[` / `]`                          |
| Quit                             | `Esc`                              |

The computer keyboard can only reach two octaves at a time (the currently
active range is shown at the top of the window and highlighted with small
letters on the keys) — use `[` and `]` to slide that window up and down the
full 88-key range. The mouse can always play any of the 88 keys directly,
regardless of the active keyboard octave.

## How it works

- The full 88-key layout is generated from standard MIDI note numbers
  (A0 = MIDI 21 through C8 = MIDI 108), so key positions, names and
  frequencies are all computed rather than hard-coded.
- Each note is synthesized once at startup with `numpy`: a handful of sine
  harmonics are summed and shaped with an exponential decay envelope (lower
  notes decay more slowly), then handed to `pygame.mixer` as a `Sound`.
- `pygame.mixer` is configured with 64 channels so multiple notes — chords,
  fast runs, sustained low notes under a melody — can all play at once.
