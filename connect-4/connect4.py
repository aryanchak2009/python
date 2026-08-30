"""
CONNECT FOUR
============
A polished Connect 4 clone built with pygame, playable locally.

Features:
- Two-player hot-seat mode, or Player vs. Computer (minimax + alpha-beta AI)
- Smooth falling-piece animation with a bit of bounce
- Mouse or keyboard controls, with a hover/column indicator
- Winning line is highlighted with a pulsing glow
- Running score across rematches (press R to play again)
- Procedurally synthesized sound effects (falls back to silence if
  numpy isn't available -- the game still looks/plays the same)

Controls:
  Mouse ................. move over a column, click to drop
  Left / Right ........... choose column
  Down / Space / Enter ... drop piece
  1 ....................... (title screen) two player mode
  2 ....................... (title screen) player vs computer
  R ....................... restart / rematch after a game ends
  Esc ..................... quit
"""

import math
import random
import sys

import pygame

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

ROWS = 6
COLS = 7
CELL = 100

BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

WIN_W = BOARD_W + 100
WIN_H = BOARD_H + 300

BOARD_X = (WIN_W - BOARD_W) // 2
BOARD_Y = 160

FPS = 60

EMPTY = 0
PLAYER_1 = 1
PLAYER_2 = 2

GRAVITY = 2200.0     # px/s^2
BOUNCE_DAMPING = 0.35

AI_THINK_DELAY = 0.35  # seconds of "thinking" pause before the AI drops

BG_TOP = (18, 22, 46)
BG_BOTTOM = (8, 10, 22)
BOARD_BLUE = (30, 70, 200)
BOARD_BLUE_DARK = (18, 46, 140)
HOLE_COLOR = (10, 12, 24)
RED = (226, 68, 62)
RED_DARK = (150, 34, 30)
YELLOW = (240, 200, 60)
YELLOW_DARK = (170, 130, 20)
WHITE = (240, 240, 250)
GREY = (150, 155, 175)
GLOW = (255, 255, 255)

STATE_TITLE = "title"
STATE_PLAY = "play"
STATE_GAMEOVER = "gameover"

PLAYER_COLORS = {
    PLAYER_1: (RED, RED_DARK),
    PLAYER_2: (YELLOW, YELLOW_DARK),
}


# --------------------------------------------------------------------------
# Sound (optional, synthesized -- mirrors the approach used in tetris.py)
# --------------------------------------------------------------------------

def make_tone(freq, duration, volume=0.4, kind="sine"):
    if not HAS_NUMPY:
        return None
    sample_rate = 44100
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n, False)
    if kind == "sine":
        wave = np.sin(freq * t * 2 * np.pi)
    elif kind == "square":
        wave = np.sign(np.sin(freq * t * 2 * np.pi))
    else:
        wave = np.sin(freq * t * 2 * np.pi)
    envelope = np.linspace(1, 0, n) ** 1.5
    wave = wave * envelope * volume
    audio = np.repeat((wave * 32767).astype(np.int16).reshape(-1, 1), 2, axis=1)
    return pygame.sndarray.make_sound(np.ascontiguousarray(audio))


class Sounds:
    def __init__(self):
        self.enabled = False
        self.drop = self.win = self.click = self.draw = None
        if not HAS_NUMPY:
            return
        try:
            pygame.mixer.init()
            self.drop = make_tone(220, 0.10, 0.35)
            self.click = make_tone(660, 0.05, 0.2)
            self.draw = make_tone(180, 0.35, 0.3, "square")
            self.enabled = True
        except Exception:
            self.enabled = False

    def play(self, sound):
        if self.enabled and sound is not None:
            sound.play()

    def play_win(self):
        if not self.enabled:
            return
        for f in (523, 659, 784, 1046):
            s = make_tone(f, 0.18, 0.35)
            if s:
                s.play()


# --------------------------------------------------------------------------
# Board logic
# --------------------------------------------------------------------------

def create_board():
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def is_valid_column(board, col):
    return board[0][col] == EMPTY


def valid_columns(board):
    return [c for c in range(COLS) if is_valid_column(board, c)]


def next_open_row(board, col):
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == EMPTY:
            return row
    return None


def winning_cells(board, piece):
    """Return the list of 4 (row, col) cells that win for `piece`, or None."""
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == piece for i in range(4)):
                return [(r, c + i) for i in range(4)]

    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return [(r + i, c) for i in range(4)]

    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return [(r + i, c + i) for i in range(4)]

    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return [(r - i, c + i) for i in range(4)]

    return None


def is_full(board):
    return len(valid_columns(board)) == 0


# --------------------------------------------------------------------------
# AI (minimax with alpha-beta pruning)
# --------------------------------------------------------------------------

WINDOW_LEN = 4


def evaluate_window(window, piece):
    opponent = PLAYER_2 if piece == PLAYER_1 else PLAYER_1
    score = 0
    count_piece = window.count(piece)
    count_empty = window.count(EMPTY)
    count_opp = window.count(opponent)

    if count_piece == 4:
        score += 100
    elif count_piece == 3 and count_empty == 1:
        score += 5
    elif count_piece == 2 and count_empty == 2:
        score += 2

    if count_opp == 3 and count_empty == 1:
        score -= 4

    return score


def score_position(board, piece):
    score = 0

    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_col.count(piece) * 3

    for r in range(ROWS):
        row = board[r]
        for c in range(COLS - 3):
            score += evaluate_window(row[c:c + 4], piece)

    for c in range(COLS):
        col = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            score += evaluate_window(col[r:r + 4], piece)

    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)

    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + 3 - i][c + i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score


def is_terminal_node(board):
    return (winning_cells(board, PLAYER_1) is not None or
            winning_cells(board, PLAYER_2) is not None or
            is_full(board))


def minimax(board, depth, alpha, beta, maximizing, ai_piece, human_piece):
    valid = valid_columns(board)
    terminal = is_terminal_node(board)

    if depth == 0 or terminal:
        if terminal:
            if winning_cells(board, ai_piece):
                return (None, 10_000_000)
            elif winning_cells(board, human_piece):
                return (None, -10_000_000)
            else:
                return (None, 0)
        return (None, score_position(board, ai_piece))

    if maximizing:
        value = -math.inf
        best_col = random.choice(valid)
        for col in valid:
            row = next_open_row(board, col)
            board[row][col] = ai_piece
            _, new_score = minimax(board, depth - 1, alpha, beta, False, ai_piece, human_piece)
            board[row][col] = EMPTY
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = math.inf
        best_col = random.choice(valid)
        for col in valid:
            row = next_open_row(board, col)
            board[row][col] = human_piece
            _, new_score = minimax(board, depth - 1, alpha, beta, True, ai_piece, human_piece)
            board[row][col] = EMPTY
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value


def ai_choose_column(board, ai_piece, human_piece, depth=5):
    # Take an immediate win or block an immediate loss without searching,
    # then fall back to minimax for everything else.
    for col in valid_columns(board):
        row = next_open_row(board, col)
        board[row][col] = ai_piece
        won = winning_cells(board, ai_piece) is not None
        board[row][col] = EMPTY
        if won:
            return col

    for col in valid_columns(board):
        row = next_open_row(board, col)
        board[row][col] = human_piece
        lost = winning_cells(board, human_piece) is not None
        board[row][col] = EMPTY
        if lost:
            return col

    col, _ = minimax(board, depth, -math.inf, math.inf, True, ai_piece, human_piece)
    return col


# --------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------

def draw_vertical_gradient(surface, top_color, bottom_color):
    h = surface.get_height()
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3))
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))


def cell_center(row, col):
    x = BOARD_X + col * CELL + CELL // 2
    y = BOARD_Y + row * CELL + CELL // 2
    return x, y


def draw_disc(surface, x, y, radius, color, dark_color, glow=False, glow_t=0.0):
    if glow:
        pulse = 6 + 4 * math.sin(glow_t * 6)
        pygame.draw.circle(surface, GLOW, (int(x), int(y)), int(radius + pulse), width=4)
    pygame.draw.circle(surface, dark_color, (int(x), int(y + 3)), radius)
    pygame.draw.circle(surface, color, (int(x), int(y)), radius)
    highlight = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(highlight, (255, 255, 255, 70), (int(radius * 0.65), int(radius * 0.6)), int(radius * 0.4))
    surface.blit(highlight, (x - radius, y - radius))


def draw_board_frame(surface):
    pygame.draw.rect(
        surface, BOARD_BLUE_DARK,
        (BOARD_X - 10, BOARD_Y - 10, BOARD_W + 20, BOARD_H + 20),
        border_radius=18,
    )
    pygame.draw.rect(
        surface, BOARD_BLUE,
        (BOARD_X, BOARD_Y, BOARD_W, BOARD_H),
        border_radius=14,
    )


def draw_board_holes(surface, board, radius=42):
    for r in range(ROWS):
        for c in range(COLS):
            x, y = cell_center(r, c)
            piece = board[r][c]
            if piece == EMPTY:
                pygame.draw.circle(surface, HOLE_COLOR, (x, y), radius)
            else:
                color, dark = PLAYER_COLORS[piece]
                draw_disc(surface, x, y, radius, color, dark)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(60, 260)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 120
        self.life = random.uniform(0.6, 1.2)
        self.max_life = self.life
        self.color = color
        self.size = random.uniform(3, 6)

    def update(self, dt):
        self.vy += 500 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        t = max(self.life / self.max_life, 0)
        color = self.color
        alpha = int(255 * t)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (self.size, self.size), self.size * t + 1)
        surface.blit(s, (self.x - self.size, self.y - self.size))


class FallingPiece:
    def __init__(self, col, target_row, piece):
        self.col = col
        self.target_row = target_row
        self.piece = piece
        self.x = BOARD_X + col * CELL + CELL // 2
        self.y = BOARD_Y - CELL // 2
        self.vy = 0.0
        self.settled = False
        self.bounces = 0

    @property
    def target_y(self):
        return BOARD_Y + self.target_row * CELL + CELL // 2

    def update(self, dt):
        self.vy += GRAVITY * dt
        self.y += self.vy * dt
        if self.y >= self.target_y:
            self.y = self.target_y
            if abs(self.vy) > 260 and self.bounces < 2:
                self.vy = -self.vy * BOUNCE_DAMPING
                self.bounces += 1
            else:
                self.settled = True


# --------------------------------------------------------------------------
# Game
# --------------------------------------------------------------------------

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Connect Four")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("arial", 56, bold=True)
        self.font_med = pygame.font.SysFont("arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("arial", 22)
        self.font_tiny = pygame.font.SysFont("arial", 16)

        self.bg = pygame.Surface((WIN_W, WIN_H))
        draw_vertical_gradient(self.bg, BG_TOP, BG_BOTTOM)

        self.sounds = Sounds()

        self.vs_ai = False
        self.scores = {PLAYER_1: 0, PLAYER_2: 0}
        self.time = 0.0
        self.new_game()
        self.state = STATE_TITLE

    # -- game lifecycle ----------------------------------------------------

    def new_game(self):
        self.board = create_board()
        self.turn = PLAYER_1
        self.hover_col = COLS // 2
        self.falling = None
        self.winner = None
        self.win_line = None
        self.particles = []
        self.ai_timer = 0.0
        self.game_over_at = None

    def start_game(self, vs_ai):
        self.vs_ai = vs_ai
        self.new_game()
        self.state = STATE_PLAY

    # -- move handling -------------------------------------------------

    def try_drop(self, col):
        if self.falling is not None or self.state != STATE_PLAY:
            return
        if col is None or not (0 <= col < COLS) or not is_valid_column(self.board, col):
            return
        row = next_open_row(self.board, col)
        self.falling = FallingPiece(col, row, self.turn)
        self.sounds.play(self.sounds.drop)

    def settle_falling_piece(self):
        fp = self.falling
        self.board[fp.target_row][fp.col] = fp.piece
        self.falling = None

        win = winning_cells(self.board, fp.piece)
        if win:
            self.winner = fp.piece
            self.win_line = win
            self.scores[fp.piece] += 1
            self.state = STATE_GAMEOVER
            self.game_over_at = self.time
            self.spawn_win_particles(win)
            self.sounds.play_win()
        elif is_full(self.board):
            self.winner = None
            self.win_line = None
            self.state = STATE_GAMEOVER
            self.game_over_at = self.time
            self.sounds.play(self.sounds.draw)
        else:
            self.turn = PLAYER_2 if fp.piece == PLAYER_1 else PLAYER_1
            self.ai_timer = 0.0

    def spawn_win_particles(self, cells):
        color, _ = PLAYER_COLORS[self.winner]
        for (r, c) in cells:
            x, y = cell_center(r, c)
            for _ in range(14):
                self.particles.append(Particle(x, y, color))

    def ai_is_up(self):
        return self.vs_ai and self.turn == PLAYER_2 and self.falling is None and self.state == STATE_PLAY

    # -- update / draw ----------------------------------------------------

    def update(self, dt):
        self.time += dt

        if self.falling is not None:
            self.falling.update(dt)
            if self.falling.settled:
                self.settle_falling_piece()

        if self.ai_is_up():
            self.ai_timer += dt
            if self.ai_timer >= AI_THINK_DELAY:
                col = ai_choose_column(self.board, PLAYER_2, PLAYER_1)
                self.try_drop(col)

        alive = []
        for p in self.particles:
            p.update(dt)
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self):
        self.screen.blit(self.bg, (0, 0))
        if self.state == STATE_TITLE:
            self.draw_title()
        else:
            self.draw_play()
        pygame.display.flip()

    def draw_title(self):
        title = self.font_big.render("CONNECT FOUR", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WIN_W // 2, 90)))

        draw_board_frame(self.screen)
        demo_board = create_board()
        t = self.time
        for c in range(COLS):
            fill = int((math.sin(t * 0.6 + c) + 1) / 2 * ROWS)
            for r in range(ROWS - 1, ROWS - 1 - fill, -1):
                demo_board[r][c] = PLAYER_1 if (r + c) % 2 == 0 else PLAYER_2
        draw_board_holes(self.screen, demo_board)

        lines = [
            "1  -  Two Player",
            "2  -  Player vs Computer",
            "Esc  -  Quit",
        ]
        y = BOARD_Y + BOARD_H + 40
        for line in lines:
            surf = self.font_med.render(line, True, WHITE)
            self.screen.blit(surf, surf.get_rect(center=(WIN_W // 2, y)))
            y += 38

    def draw_play(self):
        draw_board_frame(self.screen)

        if self.state == STATE_PLAY and self.falling is None:
            self.draw_hover_indicator()

        draw_board_holes(self.screen, self.board)

        if self.falling is not None:
            color, dark = PLAYER_COLORS[self.falling.piece]
            draw_disc(self.screen, self.falling.x, self.falling.y, 42, color, dark)

        if self.win_line:
            for (r, c) in self.win_line:
                x, y = cell_center(r, c)
                color, dark = PLAYER_COLORS[self.winner]
                draw_disc(self.screen, x, y, 42, color, dark, glow=True, glow_t=self.time)

        for p in self.particles:
            p.draw(self.screen)

        self.draw_hud()

        if self.state == STATE_GAMEOVER:
            self.draw_game_over_banner()

    def draw_hover_indicator(self):
        col = self.hover_col
        if col is None or not is_valid_column(self.board, col):
            return
        color, dark = PLAYER_COLORS[self.turn]
        x = BOARD_X + col * CELL + CELL // 2
        y = BOARD_Y - 50
        alpha_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(alpha_surf, (*color, 160), (45, 45), 38)
        self.screen.blit(alpha_surf, (x - 45, y - 45))

    def draw_hud(self):
        p1_label = "Player 1" if self.vs_ai else "Player 1"
        p2_label = "Computer" if self.vs_ai else "Player 2"

        name1 = self.font_small.render(f"{p1_label} (Red)", True, RED)
        name2 = self.font_small.render(f"{p2_label} (Yellow)", True, YELLOW)
        self.screen.blit(name1, (BOARD_X, 20))
        self.screen.blit(name2, (WIN_W - BOARD_X - name2.get_width(), 20))

        score1 = self.font_med.render(str(self.scores[PLAYER_1]), True, WHITE)
        score2 = self.font_med.render(str(self.scores[PLAYER_2]), True, WHITE)
        self.screen.blit(score1, (BOARD_X, 48))
        self.screen.blit(score2, (WIN_W - BOARD_X - score2.get_width(), 48))

        if self.state == STATE_PLAY:
            turn_label = "Your turn" if (self.vs_ai and self.turn == PLAYER_1) else \
                         ("Computer is thinking..." if (self.vs_ai and self.turn == PLAYER_2) else
                          f"Player {self.turn}'s turn")
            color, _ = PLAYER_COLORS[self.turn]
            turn_surf = self.font_med.render(turn_label, True, color)
            self.screen.blit(turn_surf, turn_surf.get_rect(center=(WIN_W // 2, 60)))

        hint = self.font_tiny.render("Arrows/Mouse to choose, Space/Click to drop, R to restart, Esc to quit", True, GREY)
        self.screen.blit(hint, hint.get_rect(center=(WIN_W // 2, WIN_H - 24)))

    def draw_game_over_banner(self):
        if self.winner:
            if self.vs_ai:
                text = "You win!" if self.winner == PLAYER_1 else "Computer wins!"
            else:
                text = f"Player {self.winner} wins!"
            color, _ = PLAYER_COLORS[self.winner]
        else:
            text = "It's a draw!"
            color = WHITE

        surf = self.font_big.render(text, True, color)
        shadow = self.font_big.render(text, True, (0, 0, 0))
        pos = surf.get_rect(center=(WIN_W // 2, 100))
        self.screen.blit(shadow, pos.move(2, 2))
        self.screen.blit(surf, pos)

        sub = self.font_small.render("Press R for a rematch", True, WHITE)
        self.screen.blit(sub, sub.get_rect(center=(WIN_W // 2, 140)))

    # -- input --------------------------------------------------------

    def column_from_mouse(self, mx):
        if not (BOARD_X <= mx <= BOARD_X + BOARD_W):
            return None
        return (mx - BOARD_X) // CELL

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if self.state == STATE_TITLE:
                if event.key == pygame.K_1:
                    self.start_game(vs_ai=False)
                elif event.key == pygame.K_2:
                    self.start_game(vs_ai=True)
                return

            if event.key == pygame.K_r:
                self.start_game(self.vs_ai)
                return

            if self.state != STATE_PLAY:
                return

            human_turn = (self.turn == PLAYER_1) or not self.vs_ai
            if not human_turn:
                return

            if event.key == pygame.K_LEFT:
                self.hover_col = max(0, self.hover_col - 1)
                self.sounds.play(self.sounds.click)
            elif event.key == pygame.K_RIGHT:
                self.hover_col = min(COLS - 1, self.hover_col + 1)
                self.sounds.play(self.sounds.click)
            elif event.key in (pygame.K_DOWN, pygame.K_SPACE, pygame.K_RETURN):
                self.try_drop(self.hover_col)

        elif event.type == pygame.MOUSEMOTION:
            if self.state == STATE_PLAY:
                col = self.column_from_mouse(event.pos[0])
                if col is not None:
                    self.hover_col = col

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == STATE_PLAY:
                human_turn = (self.turn == PLAYER_1) or not self.vs_ai
                if human_turn:
                    col = self.column_from_mouse(event.pos[0])
                    if col is not None:
                        self.try_drop(col)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()


def main():
    Game().run()


if __name__ == "__main__":
    main()
