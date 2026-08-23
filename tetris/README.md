# Neon Tetris

A visually rich Tetris clone built with `pygame` — beveled glossy blocks,
a ghost piece, hold/next panels, particle bursts and screen shake on line
clears, and procedurally generated sound effects.

## Run it locally

1. Make sure you have Python 3.9+ installed.
2. From this folder, install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the game:

   ```bash
   python tetris.py
   ```

A window should open. `numpy` is only used for the synthesized sound
effects — if it isn't installed the game still runs, just without audio.

## Controls

| Action           | Key(s)     |
|------------------|------------|
| Move left/right  | ← / →      |
| Soft drop        | ↓          |
| Hard drop        | Space      |
| Rotate clockwise | ↑ or X     |
| Rotate counter-clockwise | Z |
| Hold piece       | C          |
| Pause            | P          |
| Start / restart  | Enter      |
| Quit             | Esc        |

## Features

- 7-bag piece randomizer (like the modern Tetris guideline)
- Wall-kick rotation and a short lock-delay before pieces settle
- Ghost piece showing where the current piece will land
- Hold box and a 3-piece "next" preview queue
- Combo scoring, leveling (speed increases every 10 lines), and a
  score/level/lines HUD
- Particle bursts, a white flash and screen shake on line clears
  (bigger effect for a Tetris/4-line clear)
- Animated title screen and game-over screen
