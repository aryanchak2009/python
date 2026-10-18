"""
BATTLESHIP
==========
A terminal Battleship game. Guess coordinates to sink the hidden fleet.
Every hit earns points, every miss costs a life -- run out of lives and
it's game over. Sink the whole fleet to win.

Run it:
    python battleship.py
"""

import random
import string
import sys

BOARD_SIZE = 10
STARTING_LIVES = 10
POINTS_PER_HIT = 10
POINTS_PER_SINK = 50

# (name, length)
FLEET = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]

UNKNOWN, HIT, MISS = ".", "X", "o"

COLOR_HIT = "\033[91m"
COLOR_MISS = "\033[94m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"


class Ship:
    def __init__(self, name, cells):
        self.name = name
        self.cells = set(cells)
        self.hits = set()

    def register_hit(self, cell):
        self.hits.add(cell)

    def is_sunk(self):
        return self.hits == self.cells


class Board:
    def __init__(self, size=BOARD_SIZE):
        self.size = size
        self.ships = []
        self.shots = {}  # cell -> HIT or MISS
        self._place_fleet()

    def _place_fleet(self):
        for name, length in FLEET:
            while True:
                horizontal = random.choice([True, False])
                if horizontal:
                    row = random.randrange(self.size)
                    col = random.randrange(self.size - length + 1)
                    cells = [(row, col + i) for i in range(length)]
                else:
                    row = random.randrange(self.size - length + 1)
                    col = random.randrange(self.size)
                    cells = [(row + i, col) for i in range(length)]

                if not self._collides(cells):
                    self.ships.append(Ship(name, cells))
                    break

    def _collides(self, cells):
        occupied = {cell for ship in self.ships for cell in ship.cells}
        return any(cell in occupied for cell in cells)

    def ship_at(self, cell):
        for ship in self.ships:
            if cell in ship.cells:
                return ship
        return None

    def fire(self, cell):
        """Returns (result, ship_or_none) where result is HIT or MISS."""
        ship = self.ship_at(cell)
        if ship:
            self.shots[cell] = HIT
            ship.register_hit(cell)
            return HIT, ship
        self.shots[cell] = MISS
        return MISS, None

    def all_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def render(self, reveal=False):
        header = "   " + " ".join(f"{c + 1:>2}" for c in range(self.size))
        lines = [header]
        for row in range(self.size):
            letter = string.ascii_uppercase[row]
            row_cells = []
            for col in range(self.size):
                cell = (row, col)
                mark = self.shots.get(cell)
                if mark == HIT:
                    row_cells.append(f"{COLOR_HIT}{HIT:>2}{COLOR_RESET}")
                elif mark == MISS:
                    row_cells.append(f"{COLOR_MISS}{MISS:>2}{COLOR_RESET}")
                elif reveal and self.ship_at(cell):
                    row_cells.append(f"{COLOR_BOLD}{'#':>2}{COLOR_RESET}")
                else:
                    row_cells.append(f"{UNKNOWN:>2}")
            lines.append(f"{letter:<2} " + " ".join(row_cells))
        return "\n".join(lines)


def parse_coordinate(raw, size=BOARD_SIZE):
    """Parses input like 'B5' or 'b 5' into a (row, col) tuple, or None."""
    text = raw.strip().upper().replace(" ", "")
    if not text:
        return None

    letter = text[0]
    digits = text[1:]
    if letter not in string.ascii_uppercase[:size] or not digits.isdigit():
        return None

    row = string.ascii_uppercase.index(letter)
    col = int(digits) - 1
    if not (0 <= col < size):
        return None

    return row, col


def format_coordinate(cell):
    row, col = cell
    return f"{string.ascii_uppercase[row]}{col + 1}"


def play():
    print(f"{COLOR_BOLD}=== BATTLESHIP ==={COLOR_RESET}")
    print(f"Sink the fleet before you run out of lives.")
    print(f"Each hit: +{POINTS_PER_HIT} pts (+{POINTS_PER_SINK} bonus for a sunk ship).")
    print(f"Each miss: -1 life. You start with {STARTING_LIVES} lives.")
    print("Enter coordinates like B5 (row letter + column number).\n")

    board = Board()
    lives = STARTING_LIVES
    score = 0
    total_cells = sum(length for _, length in FLEET)
    hits_so_far = 0
    guessed = set()

    while lives > 0 and not board.all_sunk():
        print()
        print(board.render())
        print(f"\nScore: {score}   Lives: {lives}   "
              f"Hits: {hits_so_far}/{total_cells}")

        raw = input("\nFire at: ").strip()
        if raw.lower() in ("quit", "exit"):
            print("Abandoning ship. Goodbye!")
            return

        cell = parse_coordinate(raw)
        if cell is None:
            print("Invalid coordinate -- try something like 'B5'.")
            continue
        if cell in guessed:
            print(f"Already fired on {format_coordinate(cell)} -- pick another.")
            continue

        guessed.add(cell)
        result, ship = board.fire(cell)

        if result == HIT:
            score += POINTS_PER_HIT
            hits_so_far += 1
            if ship.is_sunk():
                score += POINTS_PER_SINK
                print(f"HIT! You sank the {ship.name}! (+{POINTS_PER_HIT + POINTS_PER_SINK} pts)")
            else:
                print(f"HIT! (+{POINTS_PER_HIT} pts)")
        else:
            lives -= 1
            print(f"Miss. {lives} {'life' if lives == 1 else 'lives'} left.")

    print()
    print(board.render(reveal=True))
    print()
    if board.all_sunk():
        print(f"{COLOR_BOLD}You sank the entire fleet! Final score: {score}{COLOR_RESET}")
    else:
        print(f"{COLOR_BOLD}Out of lives! Final score: {score}{COLOR_RESET}")


def main():
    try:
        while True:
            play()
            again = input("\nPlay again? (y/n): ").strip().lower()
            if again != "y":
                print("Thanks for playing!")
                break
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
