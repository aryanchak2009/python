// Shared geometry for rendering a piano keyboard, so the key <div>s and the
// falling-note canvas agree on exactly where each pitch lives on screen.

const WHITE_NOTE_INDEXES = new Set([0, 2, 4, 5, 7, 9, 11]);

// Local x position of each pitch class, in "white key width" units, measured
// from the C at the start of its octave. White keys sit at integer units
// (contiguous, no gaps); black keys sit at the fractional point between the
// two white keys they're wedged between.
const LOCAL_X = [0, 0.7, 1, 1.8, 2, 3, 3.7, 4, 4.8, 5, 5.8, 6];

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

export function isWhiteKey(midi) {
  return WHITE_NOTE_INDEXES.has(((midi % 12) + 12) % 12);
}

export function noteName(midi) {
  const pitchClass = ((midi % 12) + 12) % 12;
  const octave = Math.floor(midi / 12) - 1;
  return `${NOTE_NAMES[pitchClass]}${octave}`;
}

// Pitch class colors: a 12-step rainbow so each key/note has a stable,
// recognizable hue regardless of octave.
const PITCH_COLORS = [
  "#ff5f6d", "#ff8c42", "#ffc93c", "#b4e61d", "#5cdb5c", "#2ee6a6",
  "#2ed1e6", "#3f9bff", "#7d6bff", "#c05cff", "#ff5cc6", "#ff5c8a",
];

export function pitchColor(midi) {
  return PITCH_COLORS[((midi % 12) + 12) % 12];
}

// Builds the key layout for a MIDI range [minMidi, maxMidi], plus one white
// key of padding on either side so the lowest/highest notes aren't flush
// against the edge of the keyboard.
export function buildKeyboardLayout(minMidi, maxMidi, whiteKeyWidth = 34) {
  const paddedMin = Math.max(0, minMidi - 2);
  const paddedMax = Math.min(127, maxMidi + 2);
  const baseOctave = Math.floor(paddedMin / 12);

  const keys = [];
  for (let midi = paddedMin; midi <= paddedMax; midi++) {
    const pitchClass = ((midi % 12) + 12) % 12;
    const octave = Math.floor(midi / 12);
    const globalX = (octave - baseOctave) * 7 + LOCAL_X[pitchClass];
    const white = WHITE_NOTE_INDEXES.has(pitchClass);
    keys.push({
      midi,
      white,
      name: noteName(midi),
      color: pitchColor(midi),
      left: white
        ? globalX * whiteKeyWidth
        : globalX * whiteKeyWidth - (whiteKeyWidth * 0.62) / 2,
      width: white ? whiteKeyWidth : whiteKeyWidth * 0.62,
    });
  }

  const lastWhite = [...keys].reverse().find((k) => k.white);
  const totalWidth = lastWhite ? lastWhite.left + lastWhite.width : keys.length * whiteKeyWidth;

  return { keys, totalWidth, whiteKeyWidth };
}
