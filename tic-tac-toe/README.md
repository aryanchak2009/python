# Tic-Tac-Toe (Python + React)

A full-stack Tic-Tac-Toe game:

- **Backend** (`backend/`): a Python [FastAPI](https://fastapi.tiangolo.com/) service that owns all game state and rules, and can play as an unbeatable AI opponent using minimax with alpha-beta pruning.
- **Frontend** (`frontend/`): a React (Vite) single-page app that renders the board and talks to the backend over a small REST API. It has no game logic of its own — every move is validated server-side.

Modes: **Two Players** (local, alternating X/O) or **Vs Computer** (you're X, the AI is O).

## Run it on your laptop

You need Python 3.9+ and Node.js 18+ installed. Two terminals, one for each half:

### 1. Backend

```bash
cd tic-tac-toe/backend
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

This starts the API at `http://localhost:8000` (interactive docs at `http://localhost:8000/docs`).

### 2. Frontend

In a second terminal:

```bash
cd tic-tac-toe/frontend
npm install
npm run dev
```

This starts the app at `http://localhost:5173`. The Vite dev server proxies any `/api/*` request to `http://localhost:8000`, so just open `http://localhost:5173` in your browser — no extra config needed.

### Running tests

```bash
cd tic-tac-toe/backend
source .venv/bin/activate
pytest
```

### Production build

```bash
cd tic-tac-toe/frontend
npm run build      # outputs static files to frontend/dist/
```

Serve `frontend/dist/` with any static host, and point it at a deployed instance of the backend (update the API base URL / proxy target accordingly).

## Project structure

```
tic-tac-toe/
  backend/
    app.py           # FastAPI routes (create/get/move/reset game)
    game.py           # Pure game logic: rules, win detection, minimax AI
    test_game.py       # pytest unit tests for game.py
    requirements.txt
  frontend/
    src/
      App.jsx          # Top-level state + game-mode toggle
      api.js           # fetch wrappers for the backend API
      components/
        Board.jsx
        Square.jsx
      index.css
    index.html
    vite.config.js
```

## API

| Method | Path                     | Body                | Description                                  |
|--------|--------------------------|----------------------|-----------------------------------------------|
| POST   | `/api/games`              | `{ "vs_ai": bool }`  | Create a new game                             |
| GET    | `/api/games/{id}`         | –                     | Get current state                             |
| POST   | `/api/games/{id}/move`    | `{ "position": 0-8 }`| Play a move as X (AI replies automatically)   |
| POST   | `/api/games/{id}/reset`   | `{ "vs_ai": bool }`  | Reset the board, optionally change mode       |
| DELETE | `/api/games/{id}`         | –                     | Discard a game                                |

Game state is kept in memory on the backend, so restarting the server clears all games.
