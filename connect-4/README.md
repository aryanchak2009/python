# Connect Four

A polished Connect 4 clone built with `pygame` — animated falling pieces,
a pulsing glow on the winning line, particle burst on a win, and an
optional minimax AI opponent.

## Run it locally

1. Make sure you have Python 3.9+ installed.
2. From this folder, install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the game:

   ```bash
   python connect4.py
   ```

A window should open. `numpy` is only used for the synthesized sound
effects — if it isn't installed the game still runs, just without audio.

## How to play

From the title screen, choose a mode:

| Key | Mode |
|-----|------|
| 1   | Two player (hot-seat) |
| 2   | Player vs. Computer   |

Drop pieces with the mouse or the keyboard. Get four of your pieces in a
row — horizontally, vertically, or diagonally — before your opponent does.

## Controls

| Action              | Key(s)              |
|---------------------|----------------------|
| Choose column        | Mouse, ← / →        |
| Drop piece            | Click, ↓ / Space / Enter |
| Restart / rematch     | R                    |
| Quit                  | Esc                  |

## Features

- Smooth falling-piece animation with a bit of bounce on landing
- Mouse or keyboard controls with a live column-hover indicator
- Winning four-in-a-row is highlighted with a pulsing glow and a
  confetti-style particle burst
- Running score across rematches, shown in the HUD
- Player vs. Computer mode backed by a minimax + alpha-beta AI that
  always takes an immediate win and blocks an immediate loss
- Procedurally synthesized sound effects (falls back to silence if
  `numpy` isn't available)
