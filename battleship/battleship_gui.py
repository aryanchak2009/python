"""
BATTLESHIP AT SEA
=================
A visual Battleship game built with pygame. Fire on the ocean grid to
find and sink the hidden fleet -- every hit scores points, every miss
costs a life.

Run it:
    python battleship_gui.py
"""

import math
import random
import sys
import time

import pygame

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

COLS = 10
ROWS = 10
CELL = 52

GRID_X = 40
GRID_Y = 90
GRID_W = COLS * CELL
GRID_H = ROWS * CELL

SIDEBAR_X = GRID_X + GRID_W + 40
WIN_W = SIDEBAR_X + 260
WIN_H = GRID_Y + GRID_H + 40

FPS = 60

STARTING_LIVES = 10
POINTS_PER_HIT = 10
POINTS_PER_SINK = 50

FLEET = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]

# Colors
OCEAN_DEEP = (16, 58, 94)
OCEAN_LIGHT = (32, 92, 140)
GRID_LINE = (70, 130, 170)
FOG = (60, 110, 150)
MISS_COLOR = (210, 230, 240)
HIT_COLOR = (235, 90, 40)
HIT_CORE = (255, 210, 60)
SHIP_COLOR = (90, 95, 100)
SHIP_DECK = (130, 135, 140)
SUNK_COLOR = (60, 40, 40)
PANEL_BG = (12, 30, 48)
TEXT_COLOR = (230, 240, 245)
TEXT_DIM = (150, 175, 190)
LIFE_FULL = (235, 70, 70)
LIFE_EMPTY = (70, 55, 60)
BUTTON_BG = (40, 110, 150)
BUTTON_HOVER = (60, 140, 185)
WIN_COLOR = (90, 220, 140)
LOSE_COLOR = (230, 80, 80)


# --------------------------------------------------------------------------
# Game model
# --------------------------------------------------------------------------

class Ship:
    def __init__(self, name, cells):
        self.name = name
        self.cells = set(cells)
        self.hits = set()

    def is_sunk(self):
        return self.hits == self.cells


class Board:
    def __init__(self, cols=COLS, rows=ROWS):
        self.cols = cols
        self.rows = rows
        self.ships = []
        self.shots = {}  # (col, row) -> "hit" / "miss"
        self._place_fleet()

    def _place_fleet(self):
        for name, length in FLEET:
            while True:
                horizontal = random.choice([True, False])
                if horizontal:
                    row = random.randrange(self.rows)
                    col = random.randrange(self.cols - length + 1)
                    cells = [(col + i, row) for i in range(length)]
                else:
                    col = random.randrange(self.cols)
                    row = random.randrange(self.rows - length + 1)
                    cells = [(col, row + i) for i in range(length)]

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
        ship = self.ship_at(cell)
        if ship:
            self.shots[cell] = "hit"
            ship.hits.add(cell)
            return "hit", ship
        self.shots[cell] = "miss"
        return "miss", None

    def all_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)


# --------------------------------------------------------------------------
# Visual effects
# --------------------------------------------------------------------------

class Effect:
    """A short animation (splash or explosion) anchored to a cell."""

    SPLASH_DURATION = 0.5
    EXPLOSION_DURATION = 0.6

    def __init__(self, kind, cell):
        self.kind = kind  # "splash" or "explosion"
        self.cell = cell
        self.start = time.time()

    def progress(self):
        duration = self.SPLASH_DURATION if self.kind == "splash" else self.EXPLOSION_DURATION
        return min(1.0, (time.time() - self.start) / duration)

    def finished(self):
        return self.progress() >= 1.0


def cell_rect(cell):
    col, row = cell
    return pygame.Rect(GRID_X + col * CELL, GRID_Y + row * CELL, CELL, CELL)


def cell_center(cell):
    r = cell_rect(cell)
    return r.centerx, r.centery


def draw_splash(surface, cell, progress):
    cx, cy = cell_center(cell)
    for i in range(3):
        ring_progress = max(0.0, min(1.0, progress - i * 0.15))
        if ring_progress <= 0:
            continue
        radius = int(ring_progress * CELL * 0.55)
        alpha = int(255 * (1 - ring_progress))
        if radius <= 0 or alpha <= 0:
            continue
        ring_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (255, 255, 255, alpha),
                            (CELL // 2, CELL // 2), radius, width=2)
        surface.blit(ring_surf, (cx - CELL // 2, cy - CELL // 2))


def draw_explosion(surface, cell, progress):
    cx, cy = cell_center(cell)
    flash_alpha = int(255 * max(0.0, 1 - progress * 1.6))
    core_radius = int((CELL * 0.45) * (1 - 0.4 * progress))
    glow_radius = int(core_radius + 10 * progress)

    glow_surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    if flash_alpha > 0:
        pygame.draw.circle(glow_surf, (*HIT_COLOR, flash_alpha),
                            (CELL // 2, CELL // 2), glow_radius)
    pygame.draw.circle(glow_surf, (*HIT_CORE, max(0, flash_alpha)),
                        (CELL // 2, CELL // 2), max(1, core_radius - 6))
    surface.blit(glow_surf, (cx - CELL // 2, cy - CELL // 2))

    # outward sparks
    spark_count = 6
    for i in range(spark_count):
        angle = (2 * math.pi / spark_count) * i
        dist = progress * CELL * 0.6
        sx = cx + math.cos(angle) * dist
        sy = cy + math.sin(angle) * dist
        spark_alpha = int(255 * (1 - progress))
        if spark_alpha <= 0:
            continue
        spark_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(spark_surf, (*HIT_CORE, spark_alpha), (4, 4), 3)
        surface.blit(spark_surf, (sx - 4, sy - 4))


def draw_ship(surface, ship, sunk):
    xs = [c for c, _ in ship.cells]
    ys = [r for _, r in ship.cells]
    min_c, max_c = min(xs), max(xs)
    min_r, max_r = min(ys), max(ys)
    rect = pygame.Rect(
        GRID_X + min_c * CELL + 6,
        GRID_Y + min_r * CELL + 6,
        (max_c - min_c + 1) * CELL - 12,
        (max_r - min_r + 1) * CELL - 12,
    )
    body_color = SUNK_COLOR if sunk else SHIP_COLOR
    deck_color = (90, 60, 60) if sunk else SHIP_DECK
    pygame.draw.rect(surface, body_color, rect, border_radius=10)
    pygame.draw.rect(surface, deck_color, rect.inflate(-10, -10), border_radius=8)
    pygame.draw.rect(surface, (20, 20, 25), rect, width=2, border_radius=10)


# --------------------------------------------------------------------------
# UI helpers
# --------------------------------------------------------------------------

def draw_ocean_background(surface, t):
    surface.fill(OCEAN_DEEP, pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_H))
    for y in range(0, GRID_H, 10):
        frac = y / GRID_H
        shade = tuple(int(OCEAN_DEEP[i] + (OCEAN_LIGHT[i] - OCEAN_DEEP[i]) * frac)
                      for i in range(3))
        pygame.draw.line(surface, shade, (GRID_X, GRID_Y + y), (GRID_X + GRID_W, GRID_Y + y))

    for row in range(0, ROWS + 1, 2):
        base_y = GRID_Y + row * CELL
        points = []
        for x in range(0, GRID_W + 10, 10):
            offset = math.sin((x * 0.05) + t * 2 + row) * 3
            points.append((GRID_X + x, base_y + offset))
        if len(points) > 1:
            pygame.draw.lines(surface, (255, 255, 255, 40), False, points, 1)


def draw_grid_lines(surface):
    for col in range(COLS + 1):
        x = GRID_X + col * CELL
        pygame.draw.line(surface, GRID_LINE, (x, GRID_Y), (x, GRID_Y + GRID_H))
    for row in range(ROWS + 1):
        y = GRID_Y + row * CELL
        pygame.draw.line(surface, GRID_LINE, (GRID_X, y), (GRID_X + GRID_W, y))


def draw_coordinates(surface, font):
    for col in range(COLS):
        label = font.render(str(col + 1), True, TEXT_DIM)
        x = GRID_X + col * CELL + CELL // 2 - label.get_width() // 2
        surface.blit(label, (x, GRID_Y - 24))
    for row in range(ROWS):
        letter = chr(ord("A") + row)
        label = font.render(letter, True, TEXT_DIM)
        y = GRID_Y + row * CELL + CELL // 2 - label.get_height() // 2
        surface.blit(label, (GRID_X - 22, y))


def draw_hearts(surface, x, y, lives, max_lives):
    per_row = 5
    for i in range(max_lives):
        col = i % per_row
        row = i // per_row
        cx = x + col * 26
        cy = y + row * 24
        full = i < lives
        color = LIFE_FULL if full else LIFE_EMPTY
        pygame.draw.circle(surface, color, (cx, cy), 7)
        pygame.draw.circle(surface, color, (cx + 9, cy), 7)
        pygame.draw.polygon(surface, color, [(cx - 7, cy + 2), (cx + 16, cy + 2), (cx + 4.5, cy + 16)])


def draw_button(surface, rect, text, font, hovered):
    color = BUTTON_HOVER if hovered else BUTTON_BG
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, (20, 50, 70), rect, width=2, border_radius=8)
    label = font.render(text, True, TEXT_COLOR)
    surface.blit(label, (rect.centerx - label.get_width() // 2,
                          rect.centery - label.get_height() // 2))


# --------------------------------------------------------------------------
# Game
# --------------------------------------------------------------------------

class Game:
    def __init__(self):
        self.board = Board()
        self.lives = STARTING_LIVES
        self.score = 0
        self.effects = []
        self.state = "playing"  # playing, won, lost
        self.message = ""
        self.message_timer = 0

    def total_cells(self):
        return sum(length for _, length in FLEET)

    def hits_so_far(self):
        return sum(1 for mark in self.board.shots.values() if mark == "hit")

    def fire(self, cell):
        if self.state != "playing":
            return
        if cell in self.board.shots:
            self.flash_message("Already fired there")
            return

        result, ship = self.board.fire(cell)
        if result == "hit":
            self.effects.append(Effect("explosion", cell))
            self.score += POINTS_PER_HIT
            if ship.is_sunk():
                self.score += POINTS_PER_SINK
                self.flash_message(f"{ship.name} sunk! +{POINTS_PER_HIT + POINTS_PER_SINK}")
            else:
                self.flash_message(f"Hit! +{POINTS_PER_HIT}")
        else:
            self.effects.append(Effect("splash", cell))
            self.lives -= 1
            self.flash_message("Miss!")

        if self.board.all_sunk():
            self.state = "won"
        elif self.lives <= 0:
            self.state = "lost"

    def flash_message(self, text):
        self.message = text
        self.message_timer = time.time() + 1.6

    def reset(self):
        self.__init__()


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------

def main():
    pygame.init()
    pygame.display.set_caption("Battleship at Sea")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 34, bold=True)
    big_font = pygame.font.SysFont("arial", 26, bold=True)
    font = pygame.font.SysFont("arial", 20)
    small_font = pygame.font.SysFont("arial", 16)
    coord_font = pygame.font.SysFont("arial", 16, bold=True)

    game = Game()
    restart_rect = pygame.Rect(SIDEBAR_X, WIN_H - 70, 220, 44)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and game.state != "playing":
                    game.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                grid_rect = pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_H)
                if game.state == "playing" and grid_rect.collidepoint(event.pos):
                    col = (event.pos[0] - GRID_X) // CELL
                    row = (event.pos[1] - GRID_Y) // CELL
                    game.fire((col, row))
                elif game.state != "playing" and restart_rect.collidepoint(event.pos):
                    game.reset()

        t = time.time()

        screen.fill(PANEL_BG)
        draw_ocean_background(screen, t)
        draw_grid_lines(screen)
        draw_coordinates(screen, coord_font)

        # fog overlay on unknown cells, sunk ships revealed fully
        for ship in game.board.ships:
            if ship.is_sunk():
                draw_ship(screen, ship, sunk=True)

        for cell, mark in game.board.shots.items():
            rect = cell_rect(cell)
            if mark == "miss":
                pygame.draw.circle(screen, MISS_COLOR, rect.center, 5)
            elif mark == "hit" and not game.board.ship_at(cell).is_sunk():
                pygame.draw.circle(screen, HIT_COLOR, rect.center, 10)
                pygame.draw.line(screen, HIT_CORE, (rect.centerx - 6, rect.centery - 6),
                                  (rect.centerx + 6, rect.centery + 6), 3)
                pygame.draw.line(screen, HIT_CORE, (rect.centerx - 6, rect.centery + 6),
                                  (rect.centerx + 6, rect.centery - 6), 3)

        game.effects = [e for e in game.effects if not e.finished()]
        for effect in game.effects:
            if effect.kind == "splash":
                draw_splash(screen, effect.cell, effect.progress())
            else:
                draw_explosion(screen, effect.cell, effect.progress())

        # hover highlight
        grid_rect = pygame.Rect(GRID_X, GRID_Y, GRID_W, GRID_H)
        if game.state == "playing" and grid_rect.collidepoint(mouse_pos):
            col = (mouse_pos[0] - GRID_X) // CELL
            row = (mouse_pos[1] - GRID_Y) // CELL
            if (col, row) not in game.board.shots:
                hl = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                hl.fill((255, 255, 255, 40))
                screen.blit(hl, (GRID_X + col * CELL, GRID_Y + row * CELL))

        pygame.draw.rect(screen, (90, 150, 190), (GRID_X, GRID_Y, GRID_W, GRID_H), width=3)

        # Title
        title = title_font.render("BATTLESHIP AT SEA", True, TEXT_COLOR)
        screen.blit(title, (GRID_X, 30))

        # Sidebar
        sx = SIDEBAR_X
        sy = GRID_Y
        screen.blit(big_font.render("Score", True, TEXT_DIM), (sx, sy))
        screen.blit(big_font.render(str(game.score), True, TEXT_COLOR), (sx, sy + 28))

        sy += 80
        screen.blit(big_font.render("Lives", True, TEXT_DIM), (sx, sy))
        draw_hearts(screen, sx + 8, sy + 42, game.lives, STARTING_LIVES)

        sy += 100
        screen.blit(big_font.render("Fleet", True, TEXT_DIM), (sx, sy))
        sy += 32
        for ship in game.board.ships:
            sunk = ship.is_sunk()
            color = TEXT_DIM if sunk else TEXT_COLOR
            label = f"{ship.name} ({len(ship.cells)})"
            text_surf = font.render(label, True, color)
            screen.blit(text_surf, (sx, sy))
            if sunk:
                pygame.draw.line(screen, LOSE_COLOR, (sx, sy + text_surf.get_height() // 2),
                                  (sx + text_surf.get_width(), sy + text_surf.get_height() // 2), 2)
            sy += 26

        sy += 10
        hits_text = f"Hits: {game.hits_so_far()}/{game.total_cells()}"
        screen.blit(small_font.render(hits_text, True, TEXT_DIM), (sx, sy))

        # message toast
        if game.message and time.time() < game.message_timer:
            msg_surf = big_font.render(game.message, True, HIT_CORE)
            screen.blit(msg_surf, (GRID_X, GRID_Y + GRID_H + 6))

        # Game over / win overlay
        if game.state != "playing":
            overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            if game.state == "won":
                headline = "FLEET DESTROYED - YOU WIN!"
                color = WIN_COLOR
            else:
                headline = "OUT OF LIVES - GAME OVER"
                color = LOSE_COLOR

            head_surf = title_font.render(headline, True, color)
            screen.blit(head_surf, (WIN_W // 2 - head_surf.get_width() // 2, WIN_H // 2 - 80))

            score_surf = big_font.render(f"Final score: {game.score}", True, TEXT_COLOR)
            screen.blit(score_surf, (WIN_W // 2 - score_surf.get_width() // 2, WIN_H // 2 - 30))

            restart_rect.center = (WIN_W // 2, WIN_H // 2 + 40)
            draw_button(screen, restart_rect, "Play Again (Enter)", font,
                        restart_rect.collidepoint(mouse_pos))

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
