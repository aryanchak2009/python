# Piano Notes

Type a song name or paste a YouTube link, and watch it played back on an
animated virtual piano — falling note bars and glowing keys synced to the
actual audio, like a piano tutorial video.

- **Backend** (`backend/`): a Python [FastAPI](https://fastapi.tiangolo.com/) service. It resolves your
  query to a YouTube video with [`yt-dlp`](https://github.com/yt-dlp/yt-dlp), downloads the audio, and
  transcribes it into real piano note events (pitch, timing, velocity) with Spotify's open-source
  [`basic-pitch`](https://github.com/spotify/basic-pitch) polyphonic transcription model.
- **Frontend** (`frontend/`): a React (Vite) single-page app with a canvas-rendered falling-notes
  visualizer and an animated keyboard, kept in sync with the audio element via a
  `requestAnimationFrame` loop.

There is no reliable public source of ready-made piano sheet music for arbitrary songs, so this
app *listens* to the song and figures out the notes itself. That means transcription is an estimate
(AI transcription, not a hand-verified transcript) and takes real processing time — expect anywhere
from ~10 seconds to ~2 minutes depending on song length and your machine.

## Prerequisites

- Python 3.9+
- Node.js 18+
- **ffmpeg** on your `PATH` (required by `yt-dlp` to extract audio) — e.g. `brew install ffmpeg` on
  macOS, `sudo apt install ffmpeg` on Debian/Ubuntu, or download a build for Windows.
- An internet connection (to search/download audio from YouTube). Everything else runs locally.

## Run it on your laptop

Two terminals, one for each half:

### 1. Backend

```bash
cd piano-notes/backend
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

The first request will be slower while `basic-pitch` loads its model. This starts the API at
`http://localhost:8000` (interactive docs at `http://localhost:8000/docs`).

### 2. Frontend

In a second terminal:

```bash
cd piano-notes/frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` requests to
`http://localhost:8000`, so no extra configuration is needed.

### Running backend tests

```bash
cd piano-notes/backend
source .venv/bin/activate
pytest
```

(These cover the pure logic — URL detection, cache keys, note serialization — without needing
network access or the ML model.)

## How it works

1. You submit a song name or YouTube URL.
2. The backend starts a background job: `yt-dlp` resolves it (searching YouTube if you gave a plain
   name) and downloads the best-quality audio as a `.wav`, cached by a hash of your query so
   repeat searches are instant.
3. `basic-pitch` transcribes the audio into note events: `{ pitch, start, end, velocity }` for
   every note it detects, across the whole polyphonic mix (not just the melody).
4. The frontend polls the job until it's done, then renders:
   - A **keyboard** sized to the song's actual note range.
   - A **falling-notes canvas** where each note is a colored bar (color = pitch class) that
     scrolls down and lands on its key exactly when the audio reaches that moment.
   - Keys **glow** while a note is sounding, driven by the same animation loop — no polling,
     pure `requestAnimationFrame` reading the `<audio>` element's `currentTime`.
5. Songs over 10 minutes are rejected to keep transcription time reasonable.

## Notes on accuracy and limits

- Transcription quality depends on the recording — a solo piano cover transcribes far more
  cleanly than a dense full-band studio mix, since the model is picking piano-like pitches out of
  whatever audio it's given.
- This only works for songs actually findable/downloadable from YouTube.
- Results are cached on disk in `backend/cache/` (gitignored) — delete that folder to clear the
  cache.

## Project structure

```
piano-notes/
  backend/
    app.py               # FastAPI routes: create/poll a transcription job, serve audio
    transcription.py     # yt-dlp download + basic-pitch transcription
    test_transcription.py
    requirements.txt
  frontend/
    src/
      App.jsx             # Search bar + job polling + top-level layout
      api.js               # fetch wrappers for the backend API
      pianoLayout.js        # Shared keyboard geometry (key positions, colors)
      components/
        SearchBar.jsx
        StatusBanner.jsx
        PianoVisualizer.jsx
        Keyboard.jsx
        FallingNotes.jsx     # Canvas renderer + key-highlight animation loop
        PlaybackBar.jsx
      index.css
    index.html
    vite.config.js
```

## API

| Method | Path                  | Body                 | Description                                              |
|--------|------------------------|-----------------------|------------------------------------------------------------|
| POST   | `/api/songs`            | `{ "query": str }`    | Start a transcription job for a song name or YouTube URL  |
| GET    | `/api/songs/{job_id}`   | –                      | Poll job status: `pending` → `downloading` → `transcribing` → `done`/`error` |
| GET    | `/api/audio/{filename}`| –                      | Serves the cached `.wav` audio for playback                |

Jobs are kept in memory on the backend, so restarting the server clears in-flight jobs (cached
audio files on disk are unaffected).
