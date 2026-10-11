"""Starfall: dodge the asteroids, survive with 4 lives, rack up score."""

import math
import random
import sys

import pygame

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

WIDTH, HEIGHT = 900, 700
FPS = 60
STARTING_LIVES = 4
SHIP_RADIUS = 14
INVINCIBLE_SECONDS = 1.5
SHIP_SPEED = 320  # pixels per second

BG_COLOR = (6, 8, 20)
SHIP_COLOR = (90, 220, 255)
THRUST_COLOR = (255, 170, 60)
TEXT_COLOR = (230, 236, 250)
DIM_TEXT = (150, 160, 190)
DANGER_COLOR = (255, 90, 90)
HEART_COLOR = (255, 90, 120)
HEART_EMPTY = (60, 40, 55)

ASTEROID_COLORS = [
    (150, 120, 110),
    (170, 140, 100),
    (130, 110, 140),
    (110, 150, 160),
]

BONUS_RADIUS = 13
BONUS_COLOR = (255, 215, 60)
BONUS_GLOW = (255, 235, 150)
BONUS_SCORE = 50


def make_tone(freq, duration, volume=0.25, kind="sine"):
    if not HAS_NUMPY:
        return None
    sample_rate = 44100
    n = int(sample_rate * duration)
    t = np.linspace(0, duration, n, False)
    if kind == "sine":
        wave = np.sin(freq * 2 * np.pi * t)
    elif kind == "noise":
        wave = np.random.uniform(-1, 1, n)
    else:
        wave = np.sign(np.sin(freq * 2 * np.pi * t))
    fade = min(n, 400)
    envelope = np.ones(n)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] *= np.linspace(1, 0, fade)
    wave = (wave * envelope * volume * 32767).astype(np.int16)
    stereo = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


class Starfield:
    def __init__(self, count=140):
        self.stars = []
        for _ in range(count):
            self.stars.append([
                random.uniform(0, WIDTH),
                random.uniform(0, HEIGHT),
                random.uniform(20, 90),   # drift speed
                random.uniform(1, 3),     # size
            ])

    def update(self, dt):
        for star in self.stars:
            star[1] += star[2] * dt
            if star[1] > HEIGHT:
                star[1] = 0
                star[0] = random.uniform(0, WIDTH)

    def draw(self, surface):
        for x, y, speed, size in self.stars:
            brightness = int(120 + min(speed, 90))
            pygame.draw.circle(surface, (brightness, brightness, min(255, brightness + 40)), (int(x), int(y)), int(size))


class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, 260)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.3, 0.7)
        self.age = 0.0
        self.color = color
        self.size = random.uniform(2, 4)

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.96
        self.vy *= 0.96

    @property
    def alive(self):
        return self.age < self.life

    def draw(self, surface):
        t = 1 - self.age / self.life
        if t <= 0:
            return
        r, g, b = self.color
        color = (int(r * t + 10), int(g * t + 10), int(b * t + 10))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), max(1, int(self.size * t * 2)))


class Ship:
    def __init__(self):
        self.x = WIDTH / 2
        self.y = HEIGHT - 100
        self.heading = -math.pi / 2
        self.invincible_timer = 0.0
        self.thrusting = False

    def update(self, dt, keys):
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        self.thrusting = dx != 0 or dy != 0
        if self.thrusting:
            length = math.hypot(dx, dy)
            dx, dy = dx / length, dy / length
            self.heading = math.atan2(dy, dx)
            self.x += dx * SHIP_SPEED * dt
            self.y += dy * SHIP_SPEED * dt

        margin = SHIP_RADIUS
        self.x = max(margin, min(WIDTH - margin, self.x))
        self.y = max(margin, min(HEIGHT - margin, self.y))

        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    @property
    def invincible(self):
        return self.invincible_timer > 0

    def hit(self):
        self.invincible_timer = INVINCIBLE_SECONDS

    def draw(self, surface):
        if self.invincible and int(self.invincible_timer * 10) % 2 == 0:
            return

        tip = (self.x + math.cos(self.heading) * SHIP_RADIUS * 1.6,
               self.y + math.sin(self.heading) * SHIP_RADIUS * 1.6)
        left = (self.x + math.cos(self.heading + 2.5) * SHIP_RADIUS,
                self.y + math.sin(self.heading + 2.5) * SHIP_RADIUS)
        right = (self.x + math.cos(self.heading - 2.5) * SHIP_RADIUS,
                 self.y + math.sin(self.heading - 2.5) * SHIP_RADIUS)
        back = (self.x - math.cos(self.heading) * SHIP_RADIUS * 0.4,
                self.y - math.sin(self.heading) * SHIP_RADIUS * 0.4)

        if self.thrusting:
            flame_tip = (self.x - math.cos(self.heading) * SHIP_RADIUS * (2.2 + random.random()),
                         self.y - math.sin(self.heading) * SHIP_RADIUS * (2.2 + random.random()))
            pygame.draw.polygon(surface, THRUST_COLOR, [left, flame_tip, right])

        pygame.draw.polygon(surface, SHIP_COLOR, [tip, left, back, right])
        pygame.draw.polygon(surface, (255, 255, 255), [tip, left, back, right], width=1)


class Asteroid:
    def __init__(self, speed_mult):
        self.radius = random.uniform(16, 36)
        edge = random.choice(["top", "left", "right"])
        if edge == "top":
            self.x = random.uniform(0, WIDTH)
            self.y = -self.radius
        elif edge == "left":
            self.x = -self.radius
            self.y = random.uniform(0, HEIGHT * 0.7)
        else:
            self.x = WIDTH + self.radius
            self.y = random.uniform(0, HEIGHT * 0.7)

        target_x = random.uniform(WIDTH * 0.15, WIDTH * 0.85)
        target_y = random.uniform(HEIGHT * 0.5, HEIGHT + 60)
        angle = math.atan2(target_y - self.y, target_x - self.x)
        base_speed = random.uniform(70, 150) * speed_mult
        self.vx = math.cos(angle) * base_speed
        self.vy = math.sin(angle) * base_speed

        self.color = random.choice(ASTEROID_COLORS)
        self.rotation = random.uniform(0, math.tau)
        self.spin = random.uniform(-2, 2)
        sides = random.randint(7, 10)
        self.shape = [
            (1 + random.uniform(-0.2, 0.2)) for _ in range(sides)
        ]
        self.passed = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.spin * dt

    @property
    def offscreen(self):
        return (self.y > HEIGHT + self.radius * 2 or
                self.x < -self.radius * 2 or
                self.x > WIDTH + self.radius * 2)

    def draw(self, surface):
        points = []
        n = len(self.shape)
        for i, factor in enumerate(self.shape):
            a = self.rotation + (math.tau * i / n)
            r = self.radius * factor
            points.append((self.x + math.cos(a) * r, self.y + math.sin(a) * r))
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (20, 20, 25), points, width=2)


class Bonus:
    def __init__(self):
        edge = random.choice(["top", "left", "right"])
        if edge == "top":
            self.x = random.uniform(0, WIDTH)
            self.y = -BONUS_RADIUS
        elif edge == "left":
            self.x = -BONUS_RADIUS
            self.y = random.uniform(0, HEIGHT * 0.7)
        else:
            self.x = WIDTH + BONUS_RADIUS
            self.y = random.uniform(0, HEIGHT * 0.7)

        target_x = random.uniform(WIDTH * 0.15, WIDTH * 0.85)
        target_y = random.uniform(HEIGHT * 0.5, HEIGHT + 60)
        angle = math.atan2(target_y - self.y, target_x - self.x)
        speed = random.uniform(55, 100)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.radius = BONUS_RADIUS
        self.rotation = random.uniform(0, math.tau)
        self.pulse = random.uniform(0, math.tau)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += 1.8 * dt
        self.pulse += 6 * dt

    @property
    def offscreen(self):
        return (self.y > HEIGHT + self.radius * 2 or
                self.x < -self.radius * 2 or
                self.x > WIDTH + self.radius * 2)

    def draw(self, surface):
        glow_r = int(self.radius * (1.6 + 0.2 * math.sin(self.pulse)))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*BONUS_GLOW, 70), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (self.x - glow_r, self.y - glow_r))

        points = []
        for i in range(10):
            a = self.rotation + math.pi * i / 5
            r = self.radius if i % 2 == 0 else self.radius * 0.45
            points.append((self.x + math.cos(a) * r, self.y + math.sin(a) * r))
        pygame.draw.polygon(surface, BONUS_COLOR, points)
        pygame.draw.polygon(surface, (255, 255, 255), points, width=1)


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.sound_ok = HAS_NUMPY
        except pygame.error:
            self.sound_ok = False

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Starfall")
        self.clock = pygame.time.Clock()
        self.big_font = pygame.font.SysFont("arial", 56, bold=True)
        self.mid_font = pygame.font.SysFont("arial", 30, bold=True)
        self.small_font = pygame.font.SysFont("arial", 20)

        if self.sound_ok:
            self.hit_sound = make_tone(140, 0.35, volume=0.35, kind="noise")
            self.dodge_sound = make_tone(880, 0.08, volume=0.15)
            self.gameover_sound = make_tone(90, 0.8, volume=0.3, kind="square")
            self.bonus_sound = make_tone(1320, 0.15, volume=0.25)
        else:
            self.hit_sound = self.dodge_sound = self.gameover_sound = self.bonus_sound = None

        self.reset()
        self.state = "START"

    def reset(self):
        self.ship = Ship()
        self.starfield = Starfield()
        self.asteroids = []
        self.bonuses = []
        self.particles = []
        self.lives = STARTING_LIVES
        self.score = 0.0
        self.spawn_timer = 0.0
        self.bonus_timer = random.uniform(2.0, 4.0)
        self.elapsed = 0.0

    def play_sound(self, sound):
        if sound is not None:
            sound.play()

    def difficulty(self):
        return 1 + self.elapsed / 45.0

    def spawn_interval(self):
        return max(0.25, 0.9 - self.elapsed / 60.0)

    def explode(self, x, y, color):
        for _ in range(22):
            self.particles.append(Particle(x, y, color))

    def update(self, dt, keys):
        self.starfield.update(dt)

        if self.state != "PLAYING":
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if p.alive]
            return

        self.elapsed += dt
        self.score += dt * 10 * self.difficulty()

        self.ship.update(dt, keys)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.spawn_interval()
            self.asteroids.append(Asteroid(self.difficulty()))

        for asteroid in self.asteroids:
            asteroid.update(dt)

        survivors = []
        for asteroid in self.asteroids:
            if asteroid.offscreen:
                if not self.ship.invincible:
                    self.score += 15
                    self.play_sound(self.dodge_sound)
                continue

            dist = math.hypot(asteroid.x - self.ship.x, asteroid.y - self.ship.y)
            if dist < asteroid.radius + SHIP_RADIUS * 0.8 and not self.ship.invincible:
                self.lives -= 1
                self.ship.hit()
                self.explode(asteroid.x, asteroid.y, asteroid.color)
                self.play_sound(self.hit_sound)
                if self.lives <= 0:
                    self.state = "GAME_OVER"
                    self.play_sound(self.gameover_sound)
                continue

            survivors.append(asteroid)
        self.asteroids = survivors

        self.bonus_timer -= dt
        if self.bonus_timer <= 0:
            self.bonus_timer = random.uniform(2.5, 4.5)
            self.bonuses.append(Bonus())

        for bonus in self.bonuses:
            bonus.update(dt)

        remaining_bonuses = []
        for bonus in self.bonuses:
            dist = math.hypot(bonus.x - self.ship.x, bonus.y - self.ship.y)
            if dist < bonus.radius + SHIP_RADIUS:
                self.score += BONUS_SCORE
                self.explode(bonus.x, bonus.y, BONUS_COLOR)
                self.play_sound(self.bonus_sound)
                continue
            if bonus.offscreen:
                continue
            remaining_bonuses.append(bonus)
        self.bonuses = remaining_bonuses

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw_hud(self):
        score_surf = self.mid_font.render(f"Score: {int(self.score)}", True, TEXT_COLOR)
        self.screen.blit(score_surf, (20, 16))

        for i in range(STARTING_LIVES):
            color = HEART_COLOR if i < self.lives else HEART_EMPTY
            cx = WIDTH - 30 - i * 32
            cy = 32
            pygame.draw.circle(self.screen, color, (cx - 6, cy), 8)
            pygame.draw.circle(self.screen, color, (cx + 6, cy), 8)
            pygame.draw.polygon(self.screen, color, [(cx - 13, cy + 2), (cx + 13, cy + 2), (cx, cy + 18)])

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.starfield.draw(self.screen)

        for bonus in self.bonuses:
            bonus.draw(self.screen)
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        for p in self.particles:
            p.draw(self.screen)

        if self.state in ("PLAYING", "GAME_OVER"):
            self.ship.draw(self.screen)
            self.draw_hud()

        if self.state == "START":
            self.draw_center_text(
                "STARFALL",
                "Dodge the asteroids. Arrow keys / WASD to move.",
                "Press ENTER to launch",
            )
        elif self.state == "GAME_OVER":
            self.draw_overlay()
            self.draw_center_text(
                "GAME OVER",
                f"Final score: {int(self.score)}",
                "Press ENTER to try again, ESC to quit",
                title_color=DANGER_COLOR,
            )
        elif self.state == "PAUSED":
            self.draw_overlay()
            self.draw_center_text("PAUSED", "", "Press P to resume")

        pygame.display.flip()

    def draw_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

    def draw_center_text(self, title, subtitle, hint, title_color=TEXT_COLOR):
        title_surf = self.big_font.render(title, True, title_color)
        self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 60)))

        if subtitle:
            sub_surf = self.mid_font.render(subtitle, True, TEXT_COLOR)
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2)))

        hint_surf = self.small_font.render(hint, True, DIM_TEXT)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 50)))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_RETURN:
                        if self.state in ("START", "GAME_OVER"):
                            self.reset()
                            self.state = "PLAYING"
                    if event.key == pygame.K_p and self.state in ("PLAYING", "PAUSED"):
                        self.state = "PAUSED" if self.state == "PLAYING" else "PLAYING"

            keys = pygame.key.get_pressed()
            self.update(dt, keys)
            self.draw()


if __name__ == "__main__":
    Game().run()
