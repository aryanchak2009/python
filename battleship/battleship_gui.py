"""
BATTLESHIP AT SEA
=================
A visual, arcade-style Battleship game built with pygame. Ships sail
in plain sight on the ocean -- click directly on one to hit it, click
open water and you miss. Every hit scores points, every miss costs a
life.

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

OCEAN_X = 40
OCEAN_Y = 90
OCEAN_W = 640
OCEAN_H = 520

SIDEBAR_X = OCEAN_X + OCEAN_W + 40
WIN_W = SIDEBAR_X + 260
WIN_H = OCEAN_Y + OCEAN_H + 40

FPS = 60

STARTING_LIVES = 10
POINTS_PER_HIT = 10
POINTS_PER_SINK = 50

# (name, hit points, color)
FLEET = [
    ("Carrier", 5, (80, 85, 95)),
    ("Battleship", 4, (70, 100, 130)),
    ("Cruiser", 3, (95, 110, 70)),
    ("Submarine", 3, (55, 95, 100)),
    ("Destroyer", 2, (105, 85, 70)),
]

SINK_DURATION = 1.2

# Colors
OCEAN_DEEP = (16, 58, 94)
OCEAN_LIGHT = (32, 92, 140)
PANEL_BG = (12, 30, 48)
TEXT_COLOR = (230, 240, 245)
TEXT_DIM = (150, 175, 190)
LIFE_FULL = (235, 70, 70)
LIFE_EMPTY = (70, 55, 60)
BUTTON_BG = (40, 110, 150)
BUTTON_HOVER = (60, 140, 185)
WIN_COLOR = (90, 220, 140)
LOSE_COLOR = (230, 80, 80)
HIT_COLOR = (235, 90, 40)
HIT_CORE = (255, 210, 60)
WRECK_COLOR = (40, 40, 45)
DECK_LIT = (235, 230, 200)
DECK_DAMAGED = (60, 55, 50)


# --------------------------------------------------------------------------
# Game model
# --------------------------------------------------------------------------

class Ship:
    def __init__(self, name, hp, color, lane_y, ocean_rect):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.color = color
        self.lane_y = lane_y
        self.width = 44 + hp * 26
        self.height = 38
        self.x = random.uniform(ocean_rect.left, ocean_rect.right - self.width)
        speed = random.uniform(28, 55)
        self.vx = speed if random.random() < 0.5 else -speed
        self.bob_phase = random.uniform(0, math.tau)
        self.sunk = False
        self.sink_start = None

    def rect(self):
        return pygame.Rect(int(self.x), int(self.lane_y - self.height / 2),
                            self.width, self.height)

    def is_sunk(self):
        return self.sunk

    def update(self, dt, ocean_rect):
        if self.sunk:
            return
        self.x += self.vx * dt
        if self.x <= ocean_rect.left:
            self.x = ocean_rect.left
            self.vx = abs(self.vx)
        elif self.x + self.width >= ocean_rect.right:
            self.x = ocean_rect.right - self.width
            self.vx = -abs(self.vx)

    def register_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.sunk = True
            self.sink_start = time.time()
            return True  # sank
        return False

    def sink_progress(self):
        if not self.sunk or self.sink_start is None:
            return 0.0
        return min(1.0, (time.time() - self.sink_start) / SINK_DURATION)


# --------------------------------------------------------------------------
# Visual effects (independent of any ship)
# --------------------------------------------------------------------------

class Effect:
    SPLASH_DURATION = 0.5
    EXPLOSION_DURATION = 0.5

    def __init__(self, kind, pos):
        self.kind = kind  # "splash" or "explosion"
        self.pos = pos
        self.start = time.time()

    def progress(self):
        duration = self.SPLASH_DURATION if self.kind == "splash" else self.EXPLOSION_DURATION
        return min(1.0, (time.time() - self.start) / duration)

    def finished(self):
        return self.progress() >= 1.0


def draw_splash(surface, pos, progress):
    cx, cy = pos
    for i in range(3):
        ring_progress = max(0.0, min(1.0, progress - i * 0.15))
        if ring_progress <= 0:
            continue
        radius = int(ring_progress * 34)
        alpha = int(255 * (1 - ring_progress))
        if radius <= 0 or alpha <= 0:
            continue
        ring_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (255, 255, 255, alpha), (40, 40), radius, width=2)
        surface.blit(ring_surf, (cx - 40, cy - 40))


def draw_explosion(surface, pos, progress):
    cx, cy = pos
    flash_alpha = int(255 * max(0.0, 1 - progress * 1.6))
    core_radius = int(26 * (1 - 0.4 * progress))
    glow_radius = int(core_radius + 10 * progress)

    glow_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
    if flash_alpha > 0:
        pygame.draw.circle(glow_surf, (*HIT_COLOR, flash_alpha), (45, 45), glow_radius)
    pygame.draw.circle(glow_surf, (*HIT_CORE, max(0, flash_alpha)), (45, 45), max(1, core_radius - 6))
    surface.blit(glow_surf, (cx - 45, cy - 45))

    spark_count = 7
    for i in range(spark_count):
        angle = (2 * math.pi / spark_count) * i
        dist = progress * 36
        sx = cx + math.cos(angle) * dist
        sy = cy + math.sin(angle) * dist
        spark_alpha = int(255 * (1 - progress))
        if spark_alpha <= 0:
            continue
        spark_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(spark_surf, (*HIT_CORE, spark_alpha), (4, 4), 3)
        surface.blit(spark_surf, (sx - 4, sy - 4))


def draw_ship(surface, ship, t):
    bob = math.sin(t * 2 + ship.bob_phase) * 3
    rect = ship.rect().move(0, bob)

    hull_points = [
        (rect.left + 8, rect.bottom),
        (rect.right - 8, rect.bottom),
        (rect.right, rect.top + rect.height * 0.4),
        (rect.right - 14, rect.top),
        (rect.left + 14, rect.top),
        (rect.left, rect.top + rect.height * 0.4),
    ]
    pygame.draw.polygon(surface, ship.color, hull_points)
    pygame.draw.polygon(surface, (20, 20, 25), hull_points, width=2)

    # superstructure
    deck_rect = pygame.Rect(rect.centerx - rect.width * 0.18, rect.top - 10,
                             rect.width * 0.36, 12)
    pygame.draw.rect(surface, (190, 195, 200), deck_rect, border_radius=3)

    # damage pips showing remaining hp
    pip_w = max(6, (rect.width - 20) // ship.max_hp - 4)
    start_x = rect.left + 12
    for i in range(ship.max_hp):
        px = start_x + i * (pip_w + 4)
        pip_rect = pygame.Rect(px, rect.centery - 3, pip_w, 6)
        color = DECK_LIT if i < ship.hp else DECK_DAMAGED
        pygame.draw.rect(surface, color, pip_rect, border_radius=2)


def draw_sinking_ship(surface, ship, t):
    progress = ship.sink_progress()
    rect = ship.rect()
    temp = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
    local_rect = pygame.Rect(10, 10, rect.width, rect.height)
    hull_points = [
        (local_rect.left + 8, local_rect.bottom),
        (local_rect.right - 8, local_rect.bottom),
        (local_rect.right, local_rect.top + local_rect.height * 0.4),
        (local_rect.right - 14, local_rect.top),
        (local_rect.left + 14, local_rect.top),
        (local_rect.left, local_rect.top + local_rect.height * 0.4),
    ]
    alpha = int(255 * (1 - progress))
    color = (*ship.color, alpha)
    pygame.draw.polygon(temp, color, hull_points)
    pygame.draw.polygon(temp, (20, 20, 25, alpha), hull_points, width=2)

    angle = progress * 20
    rotated = pygame.transform.rotate(temp, angle)
    drop = progress * 30
    dest = rotated.get_rect(center=(rect.centerx, rect.centery + drop))
    surface.blit(rotated, dest)


def draw_wreck(surface, ship):
    rect = ship.rect()
    pygame.draw.ellipse(surface, WRECK_COLOR, (rect.centerx - 22, rect.centery - 8, 44, 16))
    pygame.draw.circle(surface, (210, 210, 180), (rect.centerx + 6, rect.centery - 14), 3)


# --------------------------------------------------------------------------
# Background + UI helpers
# --------------------------------------------------------------------------

def draw_ocean_background(surface, rect, t):
    surface.fill(OCEAN_DEEP, rect)
    for y in range(0, rect.height, 8):
        frac = y / rect.height
        shade = tuple(int(OCEAN_DEEP[i] + (OCEAN_LIGHT[i] - OCEAN_DEEP[i]) * frac)
                      for i in range(3))
        pygame.draw.line(surface, shade, (rect.left, rect.top + y), (rect.right, rect.top + y))

    for row in range(0, rect.height, 36):
        base_y = rect.top + row
        points = []
        for x in range(0, rect.width + 10, 10):
            offset = math.sin((x * 0.04) + t * 2 + row * 0.1) * 3
            points.append((rect.left + x, base_y + offset))
        if len(points) > 1:
            pygame.draw.lines(surface, (255, 255, 255, 40), False, points, 1)

    pygame.draw.rect(surface, (90, 150, 190), rect, width=3)


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
        self.ocean_rect = pygame.Rect(OCEAN_X, OCEAN_Y, OCEAN_W, OCEAN_H)
        self.ships = []
        self._place_fleet()
        self.lives = STARTING_LIVES
        self.score = 0
        self.effects = []
        self.state = "playing"  # playing, won, lost
        self.message = ""
        self.message_timer = 0

    def _place_fleet(self):
        order = FLEET[:]
        random.shuffle(order)
        lane_count = len(order)
        lane_height = self.ocean_rect.height / lane_count
        for i, (name, hp, color) in enumerate(order):
            lane_y = self.ocean_rect.top + lane_height * (i + 0.5)
            self.ships.append(Ship(name, hp, color, lane_y, self.ocean_rect))

    def total_hp(self):
        return sum(ship.max_hp for ship in self.ships)

    def hits_so_far(self):
        return sum(ship.max_hp - ship.hp for ship in self.ships)

    def update(self, dt):
        if self.state != "playing":
            return
        for ship in self.ships:
            ship.update(dt, self.ocean_rect)

    def fire(self, pos):
        if self.state != "playing":
            return
        if not self.ocean_rect.collidepoint(pos):
            return

        target = None
        for ship in self.ships:
            if not ship.sunk and ship.rect().collidepoint(pos):
                target = ship
                break

        if target:
            sank = target.register_hit()
            self.effects.append(Effect("explosion", pos))
            self.score += POINTS_PER_HIT
            if sank:
                self.score += POINTS_PER_SINK
                self.flash_message(f"{target.name} sunk! +{POINTS_PER_HIT + POINTS_PER_SINK}")
            else:
                self.flash_message(f"Hit! +{POINTS_PER_HIT}")
        else:
            self.effects.append(Effect("splash", pos))
            self.lives -= 1
            self.flash_message("Miss!")

        if all(ship.is_sunk() for ship in self.ships):
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

    game = Game()
    restart_rect = pygame.Rect(SIDEBAR_X, WIN_H - 70, 220, 44)

    while True:
        dt = clock.tick(FPS) / 1000.0
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
                if game.state == "playing":
                    game.fire(event.pos)
                elif restart_rect.collidepoint(event.pos):
                    game.reset()

        game.update(dt)
        t = time.time()

        screen.fill(PANEL_BG)
        draw_ocean_background(screen, game.ocean_rect, t)

        for ship in game.ships:
            if ship.sunk:
                if ship.sink_progress() < 1.0:
                    draw_sinking_ship(screen, ship, t)
                else:
                    draw_wreck(screen, ship)
            else:
                draw_ship(screen, ship, t)

        game.effects = [e for e in game.effects if not e.finished()]
        for effect in game.effects:
            if effect.kind == "splash":
                draw_splash(screen, effect.pos, effect.progress())
            else:
                draw_explosion(screen, effect.pos, effect.progress())

        if game.state == "playing" and game.ocean_rect.collidepoint(mouse_pos):
            pygame.draw.circle(screen, (255, 255, 255), mouse_pos, 14, width=1)
            pygame.draw.line(screen, (255, 255, 255), (mouse_pos[0] - 18, mouse_pos[1]),
                              (mouse_pos[0] + 18, mouse_pos[1]), 1)
            pygame.draw.line(screen, (255, 255, 255), (mouse_pos[0], mouse_pos[1] - 18),
                              (mouse_pos[0], mouse_pos[1] + 18), 1)

        title = title_font.render("BATTLESHIP AT SEA", True, TEXT_COLOR)
        screen.blit(title, (OCEAN_X, 30))

        sx = SIDEBAR_X
        sy = OCEAN_Y
        screen.blit(big_font.render("Score", True, TEXT_DIM), (sx, sy))
        screen.blit(big_font.render(str(game.score), True, TEXT_COLOR), (sx, sy + 28))

        sy += 80
        screen.blit(big_font.render("Lives", True, TEXT_DIM), (sx, sy))
        draw_hearts(screen, sx + 8, sy + 42, game.lives, STARTING_LIVES)

        sy += 100
        screen.blit(big_font.render("Fleet", True, TEXT_DIM), (sx, sy))
        sy += 32
        for ship in game.ships:
            sunk = ship.is_sunk()
            color = TEXT_DIM if sunk else TEXT_COLOR
            label = f"{ship.name} ({ship.hp}/{ship.max_hp})"
            text_surf = font.render(label, True, color)
            screen.blit(text_surf, (sx, sy))
            if sunk:
                pygame.draw.line(screen, LOSE_COLOR, (sx, sy + text_surf.get_height() // 2),
                                  (sx + text_surf.get_width(), sy + text_surf.get_height() // 2), 2)
            sy += 26

        sy += 10
        hits_text = f"Hits: {game.hits_so_far()}/{game.total_hp()}"
        screen.blit(small_font.render(hits_text, True, TEXT_DIM), (sx, sy))

        if game.message and time.time() < game.message_timer:
            msg_surf = big_font.render(game.message, True, HIT_CORE)
            screen.blit(msg_surf, (OCEAN_X, OCEAN_Y + OCEAN_H + 6))

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


if __name__ == "__main__":
    main()
