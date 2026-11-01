"""FastAPI backend for the Piano Notes app.

Accepts a song name or YouTube link, downloads the audio with yt-dlp,
transcribes it into piano note events with basic-pitch, and serves both
the notes and the audio file to the frontend for a synced visualization.

Transcription takes real time (10s-2min depending on song length and
hardware), so jobs run in a background thread and the frontend polls for
status rather than blocking on one long HTTP request.
"""
from __future__ import annotations

import os
import threading
import uuid
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from transcription import CACHE_DIR, cache_key, download_audio, transcribe

app = FastAPI(title="Piano Notes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, dict] = {}
_lock = threading.Lock()


class SongRequest(BaseModel):
    query: str


def _update(job_id: str, **fields) -> None:
    with _lock:
        jobs[job_id].update(fields)


def _run_pipeline(job_id: str, query: str) -> None:
    try:
        key = cache_key(query)
        _update(job_id, status="downloading")
        wav_path, title, duration = download_audio(query, key)

        _update(job_id, status="transcribing", title=title, duration=duration)
        notes = transcribe(wav_path)

        _update(
            job_id,
            status="done",
            title=title,
            duration=duration,
            audio_url=f"/api/audio/{key}.wav",
            notes=[n.to_dict() for n in notes],
        )
    except Exception as exc:  # noqa: BLE001 - surface any failure to the client
        _update(job_id, status="error", error=str(exc))


@app.post("/api/songs")
def create_song_job(req: SongRequest) -> dict:
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Please enter a song name or YouTube link")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending"}
    threading.Thread(target=_run_pipeline, args=(job_id, query), daemon=True).start()
    return {"job_id": job_id, **jobs[job_id]}


@app.get("/api/songs/{job_id}")
def get_song_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}


@app.get("/api/audio/{filename}")
def get_audio(filename: str) -> FileResponse:
    if "/" in filename or ".." in filename or not filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type="audio/wav")
