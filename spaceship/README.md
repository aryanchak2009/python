# Starfall

A dodge-'em-up: steer a spaceship through asteroids flying in from every
side of the screen. No shooting — just survive and rack up score.

## Run it locally

1. Make sure you have Python 3.9+ installed.
2. From this folder, install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Launch the game:

   ```bash
   python spaceship.py
   ```

A window should open. `numpy` is only used for the synthesized sound
effects — if it isn't installed the game still runs, just without audio.

## Controls

| Action        | Key(s)       |
|---------------|--------------|
| Move          | Arrow keys or WASD |
| Pause/resume  | P            |
| Start/restart | Enter        |
| Quit          | Esc          |

## How it works

- Asteroids spawn from the top, left, and right edges and fly across the
  screen on random paths, speeding up and spawning faster the longer you
  survive.
- You start with 4 lives (shown as hearts, top-right). Getting hit costs
  a life and grants a brief flickering invincibility window so you can
  get clear.
- Score climbs continuously while you're alive, with bonus points for
  every asteroid that flies past without hitting you.
- Glowing gold stars drift in alongside the asteroids — fly into one to
  grab +50 points. They never hurt you.
- The game ends when all 4 lives are gone; press Enter to try again.
