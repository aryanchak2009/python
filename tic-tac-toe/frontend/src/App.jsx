import { useCallback, useEffect, useState } from "react";
import Board from "./components/Board.jsx";
import { createGame, playMove, resetGame } from "./api.js";

function statusText(game) {
  if (game.winner) {
    return game.winner === "X" ? "You win! 🎉" : "O wins.";
  }
  if (game.is_draw) {
    return "It's a draw.";
  }
  return `${game.current_player}'s turn`;
}

export default function App() {
  const [game, setGame] = useState(null);
  const [vsAi, setVsAi] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const startNewGame = useCallback(async (vsAiOption) => {
    setLoading(true);
    setError("");
    try {
      const data = await createGame(vsAiOption);
      setGame(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    startNewGame(vsAi);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handlePlay(position) {
    if (!game || game.is_over || game.board[position]) return;
    if (game.vs_ai && game.current_player !== "X") return;

    setError("");
    try {
      const data = await playMove(game.id, position);
      setGame(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleReset() {
    if (!game) return;
    setError("");
    try {
      const data = await resetGame(game.id, vsAi);
      setGame(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleModeChange(nextVsAi) {
    setVsAi(nextVsAi);
    await startNewGame(nextVsAi);
  }

  return (
    <main className="app">
      <h1>Tic-Tac-Toe</h1>

      <div className="mode-toggle" role="group" aria-label="Game mode">
        <button
          className={vsAi ? "active" : ""}
          onClick={() => handleModeChange(true)}
        >
          Vs Computer
        </button>
        <button
          className={!vsAi ? "active" : ""}
          onClick={() => handleModeChange(false)}
        >
          Two Players
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {game && !loading ? (
        <>
          <p className="status">{statusText(game)}</p>
          <Board
            board={game.board}
            winningLine={game.winning_line}
            onPlay={handlePlay}
            disabled={game.is_over || (game.vs_ai && game.current_player !== "X")}
          />
          <button className="reset" onClick={handleReset}>
            New Game
          </button>
        </>
      ) : (
        <p className="status">Loading…</p>
      )}
    </main>
  );
}
