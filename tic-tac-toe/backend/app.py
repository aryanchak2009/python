"""FastAPI backend for the Tic-Tac-Toe game.

Keeps game state server-side (in memory), so the React frontend is a thin
client that renders whatever state the API returns. Supports human-vs-human
play and an optional minimax-powered AI opponent.
"""
from __future__ import annotations

import uuid
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from game import PLAYER_O, PLAYER_X, TicTacToe

app = FastAPI(title="Tic-Tac-Toe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

games: Dict[str, TicTacToe] = {}
game_modes: Dict[str, bool] = {}  # game_id -> vs_ai


class NewGameRequest(BaseModel):
    vs_ai: bool = False


class MoveRequest(BaseModel):
    position: int


def _serialize(game_id: str) -> dict:
    game = games[game_id]
    return {"id": game_id, "vs_ai": game_modes[game_id], **game.to_dict()}


def _maybe_play_ai_move(game_id: str) -> None:
    game = games[game_id]
    if game_modes[game_id] and not game.is_over() and game.current_player == PLAYER_O:
        move = game.best_move(PLAYER_O)
        game.make_move(move, PLAYER_O)


@app.post("/api/games")
def create_game(req: NewGameRequest) -> dict:
    game_id = str(uuid.uuid4())
    games[game_id] = TicTacToe()
    game_modes[game_id] = req.vs_ai
    return _serialize(game_id)


@app.get("/api/games/{game_id}")
def get_game(game_id: str) -> dict:
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return _serialize(game_id)


@app.post("/api/games/{game_id}/move")
def make_move(game_id: str, req: MoveRequest) -> dict:
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]
    try:
        game.make_move(req.position, PLAYER_X)
        _maybe_play_ai_move(game_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _serialize(game_id)


@app.post("/api/games/{game_id}/reset")
def reset_game(game_id: str, req: Optional[NewGameRequest] = None) -> dict:
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    games[game_id] = TicTacToe()
    if req is not None:
        game_modes[game_id] = req.vs_ai
    return _serialize(game_id)


@app.delete("/api/games/{game_id}")
def delete_game(game_id: str) -> dict:
    games.pop(game_id, None)
    game_modes.pop(game_id, None)
    return {"deleted": game_id}
