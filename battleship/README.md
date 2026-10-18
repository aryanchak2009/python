# Battleship

Two ways to play the same game: a terminal version with no dependencies,
and a visual "ships at sea" version built with `pygame`.

## Visual version (battleship_gui.py)

An animated ocean grid with explosions on hits and splashes on misses,
a sidebar tracking score, lives (as hearts) and which ships are sunk.

1. Install the one dependency:

   ```bash
   pip install -r requirements.txt
   ```

2. Launch it:

   ```bash
   python battleship_gui.py
   ```

Click a cell on the ocean grid to fire. Press `Enter`/`Space` to play
again after the game ends, or `Esc` to quit.

## Terminal version (battleship.py)

```bash
python battleship.py
```

(Requires Python 3.7+, no extra packages.)

Enter coordinates like `B5` (row letter + column number) to fire. Type
`quit` at any prompt to leave early.

## Rules (both versions)

- A hidden 10x10 board holds a fleet of 5 ships (Carrier, Battleship,
  Cruiser, Submarine, Destroyer) placed at random.
- **Hit:** +10 points, plus a +50 bonus when it sinks a ship.
- **Miss:** -1 life. You start with 10 lives.
- The game ends when you sink the whole fleet (win) or run out of
  lives (lose).
