"""
NEON TETRIS
===========
A visually rich Tetris clone built with pygame.

Features:
- Smooth gradient background with a drifting starfield
- Beveled, glossy 3D-styled blocks with per-piece neon colors
- Ghost piece, hold box, and a 3-piece "next" queue
- 7-bag randomizer, DAS key-repeat, wall-kick rotation, lock delay
- Particle bursts, screen shake and flash effects on line clears
- Procedurally synthesized sound effects (falls back to silence if
  numpy isn't available -- the game still looks/plays the same)
- Title screen, pause overlay and animated game-over screen

Controls:
  Left / Right ......... move
  Down ................. soft drop
  Up / X ................ rotate clockwise
  Z ..................... rotate counter-clockwise
  Space ................. hard drop
  C ..................... hold piece
  P ..................... pause
  Enter ................. start / restart
  Esc .................... quit
"""

import math
import random
import sys
from dataclasses import dataclass, field

import pygame

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

CELL = 32
COLS = 10
ROWS = 20

BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

WIN_W = 1000
WIN_H = 760

BOARD_X = (WIN_W - BOARD_W) // 2 + 40
BOARD_Y = 70

FPS = 60

DAS_DELAY = 0.16     # seconds before auto-repeat kicks in
DAS_REPEAT = 0.045   # seconds between repeats
LOCK_DELAY = 0.5      # seconds a piece can sit before it locks
LOCK_RESET_LIMIT = 15

# Colors -------------------------------------------------------------------

BG_TOP = (10, 8, 30)
BG_BOTTOM = (28, 12, 46)
PANEL_BG = (18, 14, 38)
PANEL_BORDER = (110, 90, 200)
GRID_LINE = (60, 50, 100)
TEXT_MAIN = (235, 232, 250)
TEXT_DIM = (150, 140, 190)
ACCENT = (255, 90, 190)

PIECE_COLORS = {
    "I": (60, 220, 235),
    "O": (245, 210, 60),
    "T": (185, 90, 235),
    "S": (95, 220, 110),
    "Z": (240, 70, 90),
    "J": (75, 110, 245),
    "L": (245, 150, 55),
}

# Tetromino rotation tables (list of 4 rotation states, each a list of
# (x, y) cell offsets inside a 4x4 bounding box).
SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

KICKS = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1), (-1, -1), (1, -1)]


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def shade(color, factor):
    return tuple(int(clamp(c * factor, 0, 255)) for c in color)


# --------------------------------------------------------------------------
# Sound
# --------------------------------------------------------------------------

class SoundBank:
    """Procedurally synthesizes simple sound effects. Silently degrades
    to no-ops if numpy or the audio device isn't available."""

    def __init__(self):
        self.enabled = False
        self.sounds = {}
        if not HAS_NUMPY:
            return
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
        except pygame.error:
            return
        self.enabled = True
        self.rate = 44100
        init_info = pygame.mixer.get_init()
        self.channels = init_info[2] if init_info else 1
        self._build()

    def _to_sound(self, data):
        audio = (data * 32767).astype(np.int16)
        if self.channels > 1:
            audio = np.repeat(audio.reshape(-1, 1), self.channels, axis=1)
            audio = np.ascontiguousarray(audio)
        return pygame.sndarray.make_sound(audio)

    def _tone(self, freq, dur, wave="sine", vol=0.35, decay=6.0, sweep=0.0):
        n = int(self.rate * dur)
        t = np.linspace(0, dur, n, False)
        f = freq + sweep * t
        if wave == "sine":
            data = np.sin(2 * np.pi * f * t)
        elif wave == "square":
            data = np.sign(np.sin(2 * np.pi * f * t))
        elif wave == "tri":
            data = 2 * np.abs(2 * (f * t - np.floor(f * t + 0.5))) - 1
        else:
            data = np.sin(2 * np.pi * f * t)
        env = np.exp(-decay * t)
        data = data * env * vol
        return self._to_sound(data)

    def _chord(self, freqs, dur, vol=0.28, decay=5.0):
        n = int(self.rate * dur)
        t = np.linspace(0, dur, n, False)
        data = np.zeros(n)
        for f in freqs:
            data += np.sin(2 * np.pi * f * t)
        data /= len(freqs)
        env = np.exp(-decay * t)
        data = data * env * vol
        return self._to_sound(data)

    def _build(self):
        self.sounds["move"] = self._tone(320, 0.05, "square", vol=0.15, decay=25)
        self.sounds["rotate"] = self._tone(480, 0.07, "tri", vol=0.2, decay=18)
        self.sounds["softdrop"] = self._tone(220, 0.04, "square", vol=0.12, decay=30)
        self.sounds["harddrop"] = self._tone(120, 0.12, "square", vol=0.3, decay=10, sweep=-200)
        self.sounds["lock"] = self._tone(180, 0.09, "tri", vol=0.22, decay=14)
        self.sounds["hold"] = self._tone(500, 0.08, "sine", vol=0.2, decay=14, sweep=200)
        self.sounds["clear1"] = self._chord([523, 659], 0.18, vol=0.3)
        self.sounds["clear2"] = self._chord([523, 659, 784], 0.22, vol=0.32)
        self.sounds["clear3"] = self._chord([523, 659, 784, 988], 0.26, vol=0.34)
        self.sounds["clear4"] = self._chord([523, 659, 784, 988, 1318], 0.4, vol=0.4, decay=3.2)
        self.sounds["levelup"] = self._chord([392, 523, 659, 784], 0.5, vol=0.35, decay=3)
        self.sounds["gameover"] = self._tone(200, 0.8, "tri", vol=0.3, decay=2.2, sweep=-140)
        self.sounds["start"] = self._chord([392, 523, 659], 0.3, vol=0.3, decay=4)

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()


# --------------------------------------------------------------------------
# Particles & screen shake
# --------------------------------------------------------------------------

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple
    size: float


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, color, count=14, speed=180, gravity=True):
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd - (80 if gravity else 0)
            life = random.uniform(0.35, 0.8)
            size = random.uniform(2.5, 6)
            self.particles.append(Particle(x, y, vx, vy, life, life, color, size))

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += 420 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    def draw(self, surf):
        for p in self.particles:
            t = p.life / p.max_life
            alpha = int(clamp(t * 255, 0, 255))
            s = max(1, p.size * t)
            spark = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            col = (*p.color, alpha)
            pygame.draw.rect(spark, col, (0, 0, s * 2, s * 2), border_radius=2)
            surf.blit(spark, (p.x - s, p.y - s))


class ScreenShake:
    def __init__(self):
        self.trauma = 0.0

    def add(self, amount):
        self.trauma = clamp(self.trauma + amount, 0, 1)

    def update(self, dt):
        if self.trauma > 0:
            self.trauma = clamp(self.trauma - dt * 2.2, 0, 1)

    def offset(self):
        if self.trauma <= 0:
            return (0, 0)
        power = self.trauma ** 2
        return (
            random.uniform(-1, 1) * 10 * power,
            random.uniform(-1, 1) * 10 * power,
        )


# --------------------------------------------------------------------------
# Piece
# --------------------------------------------------------------------------

class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.rot = 0
        self.x = 3
        self.y = -2
        self.color = PIECE_COLORS[kind]

    def cells(self, rot=None, x=None, y=None):
        rot = self.rot if rot is None else rot
        x = self.x if x is None else x
        y = self.y if y is None else y
        return [(x + cx, y + cy) for cx, cy in SHAPES[self.kind][rot % 4]]

    def clone(self):
        p = Piece(self.kind)
        p.rot, p.x, p.y = self.rot, self.x, self.y
        return p


class Bag:
    """7-bag randomizer: each of the 7 pieces appears once per bag."""

    def __init__(self):
        self.queue = []
        self._refill()

    def _refill(self):
        bag = list(SHAPES.keys())
        random.shuffle(bag)
        self.queue.extend(bag)

    def next(self):
        if len(self.queue) < 7:
            self._refill()
        return self.queue.pop(0)

    def peek(self, n):
        while len(self.queue) < n + 7:
            self._refill()
        return self.queue[:n]


# --------------------------------------------------------------------------
# Board / game logic
# --------------------------------------------------------------------------

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

    def collides(self, piece, rot=None, x=None, y=None):
        for cx, cy in piece.cells(rot, x, y):
            if cx < 0 or cx >= COLS or cy >= ROWS:
                return True
            if cy >= 0 and self.grid[cy][cx] is not None:
                return True
        return False

    def lock(self, piece):
        for cx, cy in piece.cells():
            if 0 <= cy < ROWS and 0 <= cx < COLS:
                self.grid[cy][cx] = piece.color

    def clear_lines(self):
        full_rows = [r for r in range(ROWS) if all(self.grid[r][c] is not None for c in range(COLS))]
        if not full_rows:
            return []
        new_grid = [row for r, row in enumerate(self.grid) if r not in full_rows]
        for _ in full_rows:
            new_grid.insert(0, [None for _ in range(COLS)])
        self.grid = new_grid
        return full_rows

    def ghost_y(self, piece):
        y = piece.y
        while not self.collides(piece, y=y + 1):
            y += 1
        return y


# --------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------

def draw_vertical_gradient(surf, rect, top_color, bottom_color):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        col = lerp_color(top_color, bottom_color, t)
        pygame.draw.line(surf, col, (x, y + i), (x + w, y + i))


def draw_block(surf, px, py, color, size=CELL, alpha=255, glossy=True):
    """Draws a single beveled, glossy tetromino block."""
    block = pygame.Surface((size, size), pygame.SRCALPHA)
    base = shade(color, 0.92)
    light = shade(color, 1.45)
    dark = shade(color, 0.55)

    pygame.draw.rect(block, (*base, alpha), (0, 0, size, size), border_radius=5)
    # top-left highlight
    pygame.draw.polygon(
        block,
        (*light, alpha),
        [(2, 2), (size - 2, 2), (size - 6, 6), (6, 6), (6, size - 6), (2, size - 2)],
    )
    # bottom-right shadow
    pygame.draw.polygon(
        block,
        (*dark, alpha),
        [(size - 2, 2), (size - 2, size - 2), (2, size - 2), (6, size - 6), (size - 6, size - 6), (size - 6, 6)],
    )
    # inner face
    inset = 6
    pygame.draw.rect(block, (*base, alpha), (inset, inset, size - inset * 2, size - inset * 2), border_radius=3)
    if glossy:
        gloss = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.ellipse(gloss, (255, 255, 255, int(70 * (alpha / 255))), (4, 3, size - 14, size * 0.42))
        block.blit(gloss, (0, 0))
    pygame.draw.rect(block, (*shade(color, 0.35), alpha), (0, 0, size, size), width=1, border_radius=5)
    surf.blit(block, (px, py))


def draw_ghost_block(surf, px, py, color, size=CELL):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, 45), (2, 2, size - 4, size - 4), border_radius=5)
    pygame.draw.rect(s, (*color, 150), (2, 2, size - 4, size - 4), width=2, border_radius=5)
    surf.blit(s, (px, py))


def rounded_panel(surf, rect, fill=PANEL_BG, border=PANEL_BORDER, radius=12, glow=0.0):
    x, y, w, h = rect
    if glow > 0:
        glow_surf = pygame.Surface((w + 40, h + 40), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*border, int(60 * glow)), (0, 0, w + 40, h + 40), border_radius=radius + 10)
        surf.blit(glow_surf, (x - 20, y - 20), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.rect(surf, fill, rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, width=2, border_radius=radius)


class Fonts:
    def __init__(self):
        name = pygame.font.match_font("consolas,dejavusansmono,couriernew,monospace") or None
        self.title = pygame.font.Font(name, 64)
        self.big = pygame.font.Font(name, 34)
        self.med = pygame.font.Font(name, 22)
        self.small = pygame.font.Font(name, 16)
        self.tiny = pygame.font.Font(name, 13)


def draw_text(surf, font, text, color, center=None, topleft=None, shadow=True):
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        if center:
            r = sh.get_rect(center=(center[0] + 2, center[1] + 2))
        else:
            r = sh.get_rect(topleft=(topleft[0] + 2, topleft[1] + 2))
        surf.blit(sh, r)
    img = font.render(text, True, color)
    if center:
        r = img.get_rect(center=center)
    else:
        r = img.get_rect(topleft=topleft)
    surf.blit(img, r)
    return r


# --------------------------------------------------------------------------
# Game
# --------------------------------------------------------------------------

STATE_TITLE = "title"
STATE_PLAY = "play"
STATE_PAUSE = "pause"
STATE_OVER = "over"


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Neon Tetris")
        self.clock = pygame.time.Clock()
        self.fonts = Fonts()
        self.sounds = SoundBank()
        self.particles = ParticleSystem()
        self.shake = ScreenShake()
        self.stars = [
            (random.uniform(0, WIN_W), random.uniform(0, WIN_H), random.uniform(0.5, 2.2), random.uniform(20, 70))
            for _ in range(90)
        ]
        self.bg_surface = pygame.Surface((WIN_W, WIN_H))
        draw_vertical_gradient(self.bg_surface, (0, 0, WIN_W, WIN_H), BG_TOP, BG_BOTTOM)
        self.time = 0.0
        self.state = STATE_TITLE
        self.flash_alpha = 0.0
        self.line_flash_rows = []
        self.line_flash_timer = 0.0
        self.reset_game()

    # ---- setup ----------------------------------------------------------

    def reset_game(self):
        self.board = Board()
        self.bag = Bag()
        self.current = self._spawn(self.bag.next())
        self.hold_kind = None
        self.hold_used = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.combo = -1
        self.back_to_back = False
        self.drop_timer = 0.0
        self.lock_timer = 0.0
        self.locking = False
        self.lock_resets = 0
        self.das_dir = 0
        self.das_timer = 0.0
        self.soft_dropping = False
        self.game_over_anim = 0.0

    def _spawn(self, kind):
        p = Piece(kind)
        p.x, p.y = 3, -2
        return p

    @property
    def drop_interval(self):
        return max(0.08, 1.0 - (self.level - 1) * 0.075)

    # ---- input ------------------------------------------------------

    def handle_keydown(self, key):
        if self.state == STATE_TITLE:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset_game()
                self.state = STATE_PLAY
                self.sounds.play("start")
            return
        if self.state == STATE_OVER:
            if key == pygame.K_RETURN:
                self.reset_game()
                self.state = STATE_PLAY
                self.sounds.play("start")
            return
        if key == pygame.K_p:
            if self.state == STATE_PLAY:
                self.state = STATE_PAUSE
            elif self.state == STATE_PAUSE:
                self.state = STATE_PLAY
            return
        if self.state != STATE_PLAY:
            return

        if key == pygame.K_LEFT:
            self._try_move(-1, 0)
            self.das_dir = -1
            self.das_timer = 0.0
        elif key == pygame.K_RIGHT:
            self._try_move(1, 0)
            self.das_dir = 1
            self.das_timer = 0.0
        elif key == pygame.K_DOWN:
            self.soft_dropping = True
        elif key in (pygame.K_UP, pygame.K_x):
            self._try_rotate(1)
        elif key == pygame.K_z:
            self._try_rotate(-1)
        elif key == pygame.K_SPACE:
            self._hard_drop()
        elif key == pygame.K_c:
            self._hold()

    def handle_keyup(self, key):
        if key == pygame.K_DOWN:
            self.soft_dropping = False
        if key == pygame.K_LEFT and self.das_dir == -1:
            self.das_dir = 0
        if key == pygame.K_RIGHT and self.das_dir == 1:
            self.das_dir = 0

    def _try_move(self, dx, dy):
        if not self.board.collides(self.current, x=self.current.x + dx, y=self.current.y + dy):
            self.current.x += dx
            self.current.y += dy
            if dx != 0:
                self.sounds.play("move")
            if self.locking:
                self._register_lock_reset()
            return True
        return False

    def _try_rotate(self, direction):
        new_rot = (self.current.rot + direction) % 4
        for kx, ky in KICKS:
            if not self.board.collides(self.current, rot=new_rot, x=self.current.x + kx, y=self.current.y + ky):
                self.current.rot = new_rot
                self.current.x += kx
                self.current.y += ky
                self.sounds.play("rotate")
                if self.locking:
                    self._register_lock_reset()
                return True
        return False

    def _register_lock_reset(self):
        if self.lock_resets < LOCK_RESET_LIMIT:
            self.lock_timer = 0.0
            self.lock_resets += 1

    def _hard_drop(self):
        gy = self.board.ghost_y(self.current)
        dist = gy - self.current.y
        self.current.y = gy
        self.score += dist * 2
        self.shake.add(0.28)
        self.sounds.play("harddrop")
        self._lock_piece()

    def _hold(self):
        if self.hold_used:
            return
        cur_kind = self.current.kind
        if self.hold_kind is None:
            self.hold_kind = cur_kind
            self.current = self._spawn(self.bag.next())
        else:
            self.hold_kind, cur_kind = cur_kind, self.hold_kind
            self.current = self._spawn(cur_kind)
        self.hold_used = True
        self.locking = False
        self.lock_timer = 0.0
        self.lock_resets = 0
        self.sounds.play("hold")

    # ---- update -----------------------------------------------------

    def update(self, dt):
        self.time += dt
        self.shake.update(dt)
        self.particles.update(dt)
        for i, (x, y, r, spd) in enumerate(self.stars):
            y += spd * dt
            if y > WIN_H:
                y = 0
                x = random.uniform(0, WIN_W)
            self.stars[i] = (x, y, r, spd)

        if self.line_flash_timer > 0:
            self.line_flash_timer -= dt
        self.flash_alpha = max(0.0, self.flash_alpha - dt * 3.0)

        if self.state == STATE_PLAY:
            self._update_play(dt)
        elif self.state == STATE_OVER:
            self.game_over_anim = min(1.0, self.game_over_anim + dt * 1.6)

    def _update_play(self, dt):
        # DAS auto-repeat
        if self.das_dir != 0:
            self.das_timer += dt
            if self.das_timer >= DAS_DELAY:
                while self.das_timer >= DAS_DELAY:
                    self.das_timer -= DAS_REPEAT
                    if not self._try_move(self.das_dir, 0):
                        self.das_timer = 0.0
                        break

        # gravity
        interval = self.drop_interval / (6 if self.soft_dropping else 1)
        self.drop_timer += dt
        if self.drop_timer >= interval:
            self.drop_timer = 0.0
            if not self.board.collides(self.current, y=self.current.y + 1):
                self.current.y += 1
                if self.soft_dropping:
                    self.score += 1
            else:
                self.locking = True

        on_ground = self.board.collides(self.current, y=self.current.y + 1)
        if on_ground:
            self.locking = True
            self.lock_timer += dt
            if self.lock_timer >= LOCK_DELAY:
                self._lock_piece()
        else:
            self.locking = False
            self.lock_timer = 0.0
            self.lock_resets = 0

    def _lock_piece(self):
        # If the piece comes to rest with part of it still above the
        # visible playfield, the stack has topped out ("block out").
        if any(cy < 0 for _, cy in self.current.cells()):
            self._game_over()
            return

        self.board.lock(self.current)
        self.sounds.play("lock")
        cleared = self.board.clear_lines()
        if cleared:
            self._on_clear(cleared)
        else:
            self.combo = -1

        self.hold_used = False
        self.locking = False
        self.lock_timer = 0.0
        self.lock_resets = 0
        self.drop_timer = 0.0

        next_kind = self.bag.next()
        self.current = self._spawn(next_kind)
        if self.board.collides(self.current):
            self._game_over()

    def _on_clear(self, rows):
        n = len(rows)
        self.combo += 1
        base = {1: 100, 2: 300, 3: 500, 4: 800}[n]
        gained = base * self.level + self.combo * 50 * self.level
        self.score += gained
        self.lines += n
        new_level = self.lines // 10 + 1
        if new_level > self.level:
            self.level = new_level
            self.sounds.play("levelup")

        self.sounds.play(f"clear{n}")
        self.line_flash_rows = rows
        self.line_flash_timer = 0.18
        self.flash_alpha = 0.5 if n < 4 else 0.85
        self.shake.add(0.35 if n < 4 else 0.6)

        for r in rows:
            for c in range(COLS):
                color = self.board.grid[r][c] or (255, 255, 255)
                px = BOARD_X + c * CELL + CELL / 2
                py = BOARD_Y + r * CELL + CELL / 2
                self.particles.burst(px, py, color, count=6, speed=220)

    def _game_over(self):
        self.state = STATE_OVER
        self.game_over_anim = 0.0
        self.sounds.play("gameover")

    # ---- drawing ------------------------------------------------------

    def draw(self):
        surf = self.screen
        surf.blit(self.bg_surface, (0, 0))
        self._draw_stars(surf)

        ox, oy = self.shake.offset()
        board_layer = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)

        if self.state == STATE_TITLE:
            self._draw_title(board_layer)
        else:
            self._draw_board_panel(board_layer)
            self._draw_grid(board_layer)
            self._draw_ghost(board_layer)
            self._draw_stack(board_layer)
            self._draw_current(board_layer)
            self._draw_line_flash(board_layer)
            self._draw_side_panels(board_layer)
            self.particles.draw(board_layer)

            if self.state == STATE_PAUSE:
                self._draw_pause(board_layer)
            elif self.state == STATE_OVER:
                self._draw_game_over(board_layer)

        surf.blit(board_layer, (ox, oy))

        if self.flash_alpha > 0:
            flash = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self.flash_alpha * 90)))
            surf.blit(flash, (0, 0))

        pygame.display.flip()

    def _draw_stars(self, surf):
        for x, y, r, _ in self.stars:
            tw = (math.sin(self.time * 2 + x) + 1) / 2
            alpha = int(90 + tw * 100)
            s = pygame.Surface((int(r * 2 + 2), int(r * 2 + 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (200, 190, 255, alpha), (int(r + 1), int(r + 1)), r)
            surf.blit(s, (x - r, y - r))

    def _draw_title(self, surf):
        hue_t = (math.sin(self.time * 1.3) + 1) / 2
        title_color = lerp_color((255, 90, 190), (90, 200, 255), hue_t)
        bob = math.sin(self.time * 2) * 6
        draw_text(surf, self.fonts.title, "NEON TETRIS", title_color, center=(WIN_W // 2, 230 + bob))

        preview_kinds = list(SHAPES.keys())
        spacing = 90
        start_x = WIN_W // 2 - (len(preview_kinds) - 1) * spacing / 2
        for i, k in enumerate(preview_kinds):
            wob = math.sin(self.time * 3 + i) * 8
            cx = start_x + i * spacing
            cy = 320 + wob
            for cx2, cy2 in SHAPES[k][0]:
                draw_block(surf, cx + (cx2 - 1.5) * 20, cy + (cy2 - 1.5) * 20, PIECE_COLORS[k], size=20)

        alpha = int(150 + 100 * math.sin(self.time * 3))
        prompt = self.fonts.med.render("PRESS ENTER TO START", True, TEXT_MAIN)
        prompt.set_alpha(clamp(alpha, 60, 255))
        r = prompt.get_rect(center=(WIN_W // 2, 460))
        surf.blit(prompt, r)

        lines = [
            "← →  move      ↓  soft drop      SPACE  hard drop",
            "↑ / X  rotate cw     Z  rotate ccw     C  hold     P  pause",
        ]
        for i, ln in enumerate(lines):
            draw_text(surf, self.fonts.small, ln, TEXT_DIM, center=(WIN_W // 2, 540 + i * 26))

    def _draw_board_panel(self, surf):
        rounded_panel(
            surf,
            (BOARD_X - 10, BOARD_Y - 10, BOARD_W + 20, BOARD_H + 20),
            fill=(14, 10, 30),
            border=PANEL_BORDER,
            radius=14,
            glow=0.6,
        )

    def _draw_grid(self, surf):
        for r in range(ROWS + 1):
            y = BOARD_Y + r * CELL
            pygame.draw.line(surf, GRID_LINE, (BOARD_X, y), (BOARD_X + BOARD_W, y), 1)
        for c in range(COLS + 1):
            x = BOARD_X + c * CELL
            pygame.draw.line(surf, GRID_LINE, (x, BOARD_Y), (x, BOARD_Y + BOARD_H), 1)

    def _draw_stack(self, surf):
        for r in range(ROWS):
            for c in range(COLS):
                color = self.board.grid[r][c]
                if color:
                    px = BOARD_X + c * CELL
                    py = BOARD_Y + r * CELL
                    draw_block(surf, px, py, color)

    def _draw_ghost(self, surf):
        gy = self.board.ghost_y(self.current)
        for cx, cy in self.current.cells(y=gy):
            if cy >= 0:
                px = BOARD_X + cx * CELL
                py = BOARD_Y + cy * CELL
                draw_ghost_block(surf, px, py, self.current.color)

    def _draw_current(self, surf):
        pulse = 1.0
        if self.locking:
            pulse = 0.75 + 0.25 * abs(math.sin(self.time * 14))
        for cx, cy in self.current.cells():
            if cy >= -2:
                px = BOARD_X + cx * CELL
                py = BOARD_Y + cy * CELL
                alpha = int(255 * pulse) if self.locking else 255
                draw_block(surf, px, py, self.current.color, alpha=alpha)

    def _draw_line_flash(self, surf):
        if self.line_flash_timer > 0:
            t = self.line_flash_timer / 0.18
            for r in self.line_flash_rows:
                py = BOARD_Y + r * CELL
                s = pygame.Surface((BOARD_W, CELL), pygame.SRCALPHA)
                s.fill((255, 255, 255, int(200 * t)))
                surf.blit(s, (BOARD_X, py))

    def _draw_mini_piece(self, surf, kind, cx, cy, scale=18):
        cells = SHAPES[kind][0]
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        w = (max(xs) - min(xs) + 1) * scale
        h = (max(ys) - min(ys) + 1) * scale
        ox = cx - w / 2 - min(xs) * scale
        oy = cy - h / 2 - min(ys) * scale
        for x, y in cells:
            draw_block(surf, ox + x * scale, oy + y * scale, PIECE_COLORS[kind], size=scale)

    def _draw_side_panels(self, surf):
        left_x = 40
        panel_w = BOARD_X - left_x - 30

        # HOLD panel
        hold_rect = (left_x, BOARD_Y, panel_w, 120)
        rounded_panel(surf, hold_rect, glow=0.25)
        draw_text(surf, self.fonts.small, "HOLD", TEXT_DIM, center=(left_x + panel_w / 2, BOARD_Y + 22))
        if self.hold_kind:
            self._draw_mini_piece(surf, self.hold_kind, left_x + panel_w / 2, BOARD_Y + 75)

        # SCORE panel
        score_x = BOARD_X + BOARD_W + 30
        score_w = WIN_W - score_x - 40
        score_rect = (score_x, BOARD_Y, score_w, 170)
        rounded_panel(surf, score_rect, glow=0.25)
        draw_text(surf, self.fonts.small, "SCORE", TEXT_DIM, topleft=(score_x + 18, BOARD_Y + 14))
        draw_text(surf, self.fonts.big, f"{self.score:,}", ACCENT, topleft=(score_x + 18, BOARD_Y + 34))
        draw_text(surf, self.fonts.small, "LEVEL", TEXT_DIM, topleft=(score_x + 18, BOARD_Y + 88))
        draw_text(surf, self.fonts.med, str(self.level), TEXT_MAIN, topleft=(score_x + 18, BOARD_Y + 106))
        draw_text(surf, self.fonts.small, "LINES", TEXT_DIM, topleft=(score_x + 110, BOARD_Y + 88))
        draw_text(surf, self.fonts.med, str(self.lines), TEXT_MAIN, topleft=(score_x + 110, BOARD_Y + 106))
        if self.combo > 0:
            draw_text(surf, self.fonts.small, f"COMBO x{self.combo}", (255, 210, 90), topleft=(score_x + 18, BOARD_Y + 142))

        # NEXT panel
        next_rect = (score_x, BOARD_Y + 190, score_w, 300)
        rounded_panel(surf, next_rect, glow=0.25)
        draw_text(surf, self.fonts.small, "NEXT", TEXT_DIM, center=(score_x + score_w / 2, BOARD_Y + 210))
        upcoming = self.bag.peek(3)
        for i, k in enumerate(upcoming):
            cy = BOARD_Y + 270 + i * 80
            self._draw_mini_piece(surf, k, score_x + score_w / 2, cy)

        # CONTROLS reminder
        ctl_rect = (left_x, BOARD_Y + 150, panel_w, BOARD_H - 150)
        rounded_panel(surf, ctl_rect, glow=0.1)
        draw_text(surf, self.fonts.small, "CONTROLS", TEXT_DIM, topleft=(left_x + 16, BOARD_Y + 168))
        controls = [
            ("MOVE", "← →"),
            ("SOFT DROP", "↓"),
            ("HARD DROP", "SPACE"),
            ("ROTATE CW", "↑ / X"),
            ("ROTATE CCW", "Z"),
            ("HOLD", "C"),
            ("PAUSE", "P"),
        ]
        for i, (label, key) in enumerate(controls):
            yy = BOARD_Y + 204 + i * 30
            draw_text(surf, self.fonts.tiny, label, TEXT_DIM, topleft=(left_x + 16, yy))
            draw_text(surf, self.fonts.tiny, key, TEXT_MAIN, topleft=(left_x + panel_w - 70, yy))

    def _draw_pause(self, surf):
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((5, 3, 15, 170))
        surf.blit(overlay, (0, 0))
        pulse = (math.sin(self.time * 3) + 1) / 2
        color = lerp_color((255, 90, 190), (90, 200, 255), pulse)
        draw_text(surf, self.fonts.title, "PAUSED", color, center=(WIN_W // 2, WIN_H // 2 - 20))
        draw_text(surf, self.fonts.med, "press P to resume", TEXT_DIM, center=(WIN_W // 2, WIN_H // 2 + 40))

    def _draw_game_over(self, surf):
        t = self.game_over_anim
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((5, 3, 15, int(200 * t)))
        surf.blit(overlay, (0, 0))
        drop = lerp(-60, 0, min(1.0, t * 1.6))
        draw_text(surf, self.fonts.title, "GAME OVER", (255, 90, 100), center=(WIN_W // 2, WIN_H // 2 - 70 + drop))
        if t > 0.4:
            fade = clamp((t - 0.4) / 0.6, 0, 1)
            s = int(255 * fade)
            score_txt = self.fonts.big.render(f"SCORE  {self.score:,}", True, TEXT_MAIN)
            score_txt.set_alpha(s)
            surf.blit(score_txt, score_txt.get_rect(center=(WIN_W // 2, WIN_H // 2)))
            lvl_txt = self.fonts.med.render(f"LEVEL {self.level}   LINES {self.lines}", True, TEXT_DIM)
            lvl_txt.set_alpha(s)
            surf.blit(lvl_txt, lvl_txt.get_rect(center=(WIN_W // 2, WIN_H // 2 + 44)))
        if t >= 1.0:
            alpha = int(150 + 100 * math.sin(self.time * 3))
            prompt = self.fonts.med.render("PRESS ENTER TO RESTART", True, ACCENT)
            prompt.set_alpha(clamp(alpha, 60, 255))
            surf.blit(prompt, prompt.get_rect(center=(WIN_W // 2, WIN_H // 2 + 110)))

    # ---- main loop ------------------------------------------------------

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    self.handle_keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.handle_keyup(event.key)

            self.update(dt)
            self.draw()


def main():
    Game().run()


if __name__ == "__main__":
    main()
