"""
PIANO SIMULATOR
================
A full 88-key piano you can play with the mouse or the computer keyboard,
built with pygame. Every note is synthesized on startup (no sample files
needed) using a few stacked harmonics with a plucked-string style decay
envelope, so it actually sounds like a struck note rather than a beep.

Controls:
  Mouse ................. click (and drag) any of the 88 keys to play it
  Z X C V B N M , ........ white keys of the lower active octave (C..C)
  S D   G H J ............ black keys of the lower active octave
  Q W E R T Y U I ........ white keys of the upper active octave (C..C)
  2 3   5 6 7 ............ black keys of the upper active octave
  [ / ] .................. shift the keyboard's active octave down / up
  Esc .................... quit
"""

import sys

import numpy as np
import pygame

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

SAMPLE_RATE = 44100

WHITE_KEY_WIDTH = 22
WHITE_KEY_HEIGHT = 260
BLACK_KEY_WIDTH = 14
BLACK_KEY_HEIGHT = 160

HEADER_HEIGHT = 140

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

WHITE_COLOR = (250, 250, 245)
WHITE_PRESSED = (140, 200, 255)
BLACK_COLOR = (25, 25, 30)
BLACK_PRESSED = (80, 150, 230)
BG_TOP = (30, 20, 45)
BG_BOTTOM = (10, 8, 20)
TEXT_COLOR = (235, 235, 245)
DIM_TEXT = (170, 165, 185)
OUTLINE = (10, 10, 10)

# Computer-keyboard layout: pygame key constant -> semitone offset from the
# currently active base note. Two octaves are reachable at once.
KEY_OFFSETS = {
    pygame.K_z: 0, pygame.K_s: 1, pygame.K_x: 2, pygame.K_d: 3, pygame.K_c: 4,
    pygame.K_v: 5, pygame.K_g: 6, pygame.K_b: 7, pygame.K_h: 8, pygame.K_n: 9,
    pygame.K_j: 10, pygame.K_m: 11, pygame.K_COMMA: 12,
    pygame.K_q: 12, pygame.K_2: 13, pygame.K_w: 14, pygame.K_3: 15,
    pygame.K_e: 16, pygame.K_r: 17, pygame.K_5: 18, pygame.K_t: 19,
    pygame.K_6: 20, pygame.K_y: 21, pygame.K_7: 22, pygame.K_u: 23,
    pygame.K_i: 24,
}
KEY_LABELS = {
    pygame.K_z: "Z", pygame.K_s: "S", pygame.K_x: "X", pygame.K_d: "D",
    pygame.K_c: "C", pygame.K_v: "V", pygame.K_g: "G", pygame.K_b: "B",
    pygame.K_h: "H", pygame.K_n: "N", pygame.K_j: "J", pygame.K_m: "M",
    pygame.K_COMMA: ",", pygame.K_q: "Q", pygame.K_2: "2", pygame.K_w: "W",
    pygame.K_3: "3", pygame.K_e: "E", pygame.K_r: "R", pygame.K_5: "5",
    pygame.K_t: "T", pygame.K_6: "6", pygame.K_y: "Y", pygame.K_7: "7",
    pygame.K_u: "U", pygame.K_i: "I",
}

MIN_MIDI = 21   # A0
MAX_MIDI = 108  # C8
DEFAULT_BASE_MIDI = 48  # C3


# --------------------------------------------------------------------------
# Note data / sound synthesis
# --------------------------------------------------------------------------

def midi_to_freq(midi):
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def midi_to_name(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def build_keys():
    """Return the 88 piano keys in order, each as a dict of note info."""
    keys = []
    for midi in range(MIN_MIDI, MAX_MIDI + 1):
        name = NOTE_NAMES[midi % 12]
        keys.append({
            "midi": midi,
            "freq": midi_to_freq(midi),
            "name": midi_to_name(midi),
            "black": "#" in name,
        })
    return keys


def synth_note(freq, duration=1.6):
    """Synthesize a single plucked-string style piano note as a pygame Sound."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

    harmonics = [(1, 1.00), (2, 0.55), (3, 0.30), (4, 0.16), (5, 0.08), (6, 0.04)]
    wave = np.zeros_like(t)
    for n, amp in harmonics:
        wave += amp * np.sin(2 * np.pi * freq * n * t)
    wave /= sum(amp for _, amp in harmonics)

    # Fast attack, exponential decay envelope (longer decay for low notes).
    decay_rate = 2.2 + freq / 400.0
    envelope = np.exp(-decay_rate * t)
    attack_samples = max(1, int(0.004 * SAMPLE_RATE))
    envelope[:attack_samples] *= np.linspace(0, 1, attack_samples)
    wave *= envelope

    audio = np.int16(wave * 32767 * 0.5)
    stereo = np.column_stack([audio, audio])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def layout_keys(keys):
    """Assign a pygame.Rect to every key, piano-style (black keys overlap)."""
    white_rects = []
    black_rects = []
    x = 0
    for key in keys:
        if not key["black"]:
            key["rect"] = pygame.Rect(x, HEADER_HEIGHT, WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
            white_rects.append(key)
            x += WHITE_KEY_WIDTH
        else:
            key["rect"] = pygame.Rect(
                x - BLACK_KEY_WIDTH // 2, HEADER_HEIGHT, BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT
            )
            black_rects.append(key)
    width = x
    return white_rects, black_rects, width


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
    pygame.init()
    pygame.mixer.set_num_channels(64)

    keys = build_keys()
    white_keys, black_keys, board_width = layout_keys(keys)

    width = board_width
    height = HEADER_HEIGHT + WHITE_KEY_HEIGHT + 20
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Piano Simulator")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 30, bold=True)
    info_font = pygame.font.SysFont("arial", 16)
    label_font = pygame.font.SysFont("arial", 12, bold=True)
    key_label_font = pygame.font.SysFont("arial", 11, bold=True)

    print("Synthesizing 88 piano notes, please wait...")
    sounds = {key["midi"]: synth_note(key["freq"]) for key in keys}
    by_midi = {key["midi"]: key for key in keys}
    print("Ready!")

    base_midi = DEFAULT_BASE_MIDI
    pressed_midi = set()
    mouse_down = False
    mouse_last_midi = None

    def play(midi):
        if midi in sounds:
            sounds[midi].play()
            pressed_midi.add(midi)

    def release(midi):
        pressed_midi.discard(midi)

    def key_at_pos(pos):
        for key in black_keys:
            if key["rect"].collidepoint(pos):
                return key
        for key in white_keys:
            if key["rect"].collidepoint(pos):
                return key
        return None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFTBRACKET:
                    base_midi = max(MIN_MIDI, base_midi - 12)
                elif event.key == pygame.K_RIGHTBRACKET:
                    base_midi = min(MAX_MIDI - 24, base_midi + 12)
                elif event.key in KEY_OFFSETS:
                    midi = base_midi + KEY_OFFSETS[event.key]
                    if midi not in pressed_midi:
                        play(midi)

            elif event.type == pygame.KEYUP:
                if event.key in KEY_OFFSETS:
                    release(base_midi + KEY_OFFSETS[event.key])

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
                key = key_at_pos(event.pos)
                if key:
                    play(key["midi"])
                    mouse_last_midi = key["midi"]

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_down = False
                if mouse_last_midi is not None:
                    release(mouse_last_midi)
                mouse_last_midi = None

            elif event.type == pygame.MOUSEMOTION and mouse_down:
                key = key_at_pos(event.pos)
                new_midi = key["midi"] if key else None
                if new_midi != mouse_last_midi:
                    if mouse_last_midi is not None:
                        release(mouse_last_midi)
                    if new_midi is not None:
                        play(new_midi)
                    mouse_last_midi = new_midi

        # ---- draw ----
        for y in range(height):
            t = y / height
            color = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
            pygame.draw.line(screen, color, (0, y), (width, y))

        title = title_font.render("PIANO SIMULATOR", True, TEXT_COLOR)
        screen.blit(title, (16, 12))

        octave_low = midi_to_name(base_midi)
        octave_high = midi_to_name(min(base_midi + 24, MAX_MIDI))
        info_lines = [
            "Mouse: click/drag any key   |   Keyboard octave: Z X C V B N M , / Q W E R T Y U I"
            "  (black keys: S D G H J / 2 3 5 6 7)",
            f"Active keyboard range: {octave_low} - {octave_high}   "
            "( [ shift down, ] shift up )   |   Esc: quit",
        ]
        for i, line in enumerate(info_lines):
            surf = info_font.render(line, True, DIM_TEXT)
            screen.blit(surf, (16, 54 + i * 22))

        active_keys_for_labels = {
            base_midi + off: KEY_LABELS[k] for k, off in KEY_OFFSETS.items()
        }

        for key in white_keys:
            rect = key["rect"]
            color = WHITE_PRESSED if key["midi"] in pressed_midi else WHITE_COLOR
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, OUTLINE, rect, 1)
            if key["name"] == "C":
                label = label_font.render(key["name"] + str(key["midi"] // 12 - 1), True, (90, 90, 100))
                screen.blit(label, (rect.x + 3, rect.bottom - 18))
            if key["midi"] in active_keys_for_labels:
                lab = key_label_font.render(active_keys_for_labels[key["midi"]], True, (60, 90, 150))
                screen.blit(lab, (rect.centerx - 4, rect.bottom - 34))

        for key in black_keys:
            rect = key["rect"]
            color = BLACK_PRESSED if key["midi"] in pressed_midi else BLACK_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=2)
            if key["midi"] in active_keys_for_labels:
                lab = key_label_font.render(active_keys_for_labels[key["midi"]], True, (200, 220, 255))
                screen.blit(lab, (rect.centerx - 4, rect.bottom - 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
