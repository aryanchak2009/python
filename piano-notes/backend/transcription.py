"""Audio acquisition and note transcription for the Piano Notes app.

Given a song name or a YouTube link, this module downloads the best
available audio with yt-dlp, then runs Spotify's open-source basic-pitch
model to transcribe it into individual piano note events (pitch, start
time, end time, velocity).
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from typing import List, Tuple

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
MAX_DURATION_SECONDS = 10 * 60

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


@dataclass
class Note:
    pitch: int
    start: float
    end: float
    velocity: float

    def to_dict(self) -> dict:
        return {
            "pitch": self.pitch,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "velocity": round(self.velocity, 3),
        }


def is_url(text: str) -> bool:
    return bool(_URL_RE.match(text.strip()))


def cache_key(query: str) -> str:
    normalized = query.strip().lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def download_audio(query: str, key: str) -> Tuple[str, str, float]:
    """Download the best audio for a YouTube URL or search query.

    Returns (wav_path, title, duration_seconds). Reuses a cached file for
    the same query/key if one already exists.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    wav_path = os.path.join(CACHE_DIR, f"{key}.wav")
    meta_path = os.path.join(CACHE_DIR, f"{key}.title")

    if os.path.exists(wav_path) and os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as fh:
            title, duration_str = fh.read().split("\t", 1)
        return wav_path, title, float(duration_str)

    import yt_dlp

    target = query.strip() if is_url(query) else f"ytsearch1:{query.strip()}"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(CACHE_DIR, f"{key}.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(target, download=True)
        if info and "entries" in info:
            entries = [e for e in info["entries"] if e]
            if not entries:
                raise ValueError(f"No results found for '{query}'")
            info = entries[0]

    if not os.path.exists(wav_path):
        raise RuntimeError("Audio extraction failed: no .wav file was produced")

    title = info.get("title") or query
    duration = float(info.get("duration") or 0)

    if duration > MAX_DURATION_SECONDS:
        os.remove(wav_path)
        raise ValueError(
            f"'{title}' is {duration / 60:.1f} min long. Please pick a song under "
            f"{MAX_DURATION_SECONDS // 60} minutes so transcription stays fast."
        )

    with open(meta_path, "w", encoding="utf-8") as fh:
        fh.write(f"{title}\t{duration}")

    return wav_path, title, duration


def transcribe(wav_path: str) -> List[Note]:
    """Run polyphonic piano transcription on a wav file, returning sorted Notes."""
    from basic_pitch.inference import predict  # heavy import, deferred until needed

    _, _, note_events = predict(wav_path)

    notes = [
        Note(
            pitch=int(pitch),
            start=float(start),
            end=float(end),
            velocity=float(min(max(amplitude, 0.0), 1.0)),
        )
        for start, end, pitch, amplitude, _pitch_bend in note_events
    ]
    notes.sort(key=lambda n: n.start)
    return notes
