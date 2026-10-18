# Battleship

Two ways to play the same game: a terminal version with no dependencies,
and a visual "ships at sea" version built with `pygame`.

## Visual version (battleship_gui.py)

Five ships sail in plain sight on an animated ocean, each slowly drifting
back and forth in its own lane. Click directly on a ship to hit it --
click open water and you miss. A sidebar tracks score, lives (as
hearts) and each ship's remaining hit points.

1. Install the one dependency:

   ```bash
   pip install -r requirements.txt
   ```

2. Launch it:

   ```bash
   python battleship_gui.py
   ```

Click a ship to fire at it. Press `Enter`/`Space` to play again after
the game ends, or `Esc` to quit.

## Terminal version (battleship.py)

```bash
python battleship.py
```

(Requires Python 3.7+, no extra packages.)

This version plays classic hidden-fleet Battleship: the ships are
invisible until hit. Enter coordinates like `B5` (row letter + column
number) to fire. Type `quit` at any prompt to leave early.

## Rules (both versions)

- A fleet of 5 ships (Carrier, Battleship, Cruiser, Submarine,
  Destroyer), each with hit points equal to its size (5/4/3/3/2).
- **Hit:** +10 points, plus a +50 bonus when it sinks a ship.
- **Miss:** -1 life. You start with 10 lives.
- The game ends when you sink the whole fleet (win) or run out of
  lives (lose).
