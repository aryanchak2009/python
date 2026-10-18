# Battleship

A terminal Battleship game. No dependencies beyond the Python standard
library.

## Run it locally

```bash
python battleship.py
```

(Requires Python 3.7+.)

## How it works

- A hidden 10x10 board holds a fleet of 5 ships (Carrier, Battleship,
  Cruiser, Submarine, Destroyer) placed at random.
- Enter coordinates like `B5` (row letter + column number) to fire.
- **Hit:** +10 points, plus a +50 bonus when it sinks a ship.
- **Miss:** -1 life. You start with 10 lives.
- The game ends when you sink the whole fleet (win) or run out of
  lives (lose). Type `quit` at any prompt to leave early.
- After each game you can choose to play again.
