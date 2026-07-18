"""Core Tic-Tac-Toe game logic, independent of any web framework."""
from __future__ import annotations

from typing import List, Optional

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]

EMPTY = ""
PLAYER_X = "X"
PLAYER_O = "O"


class TicTacToe:
    """Holds a 3x3 board (as a flat list of 9 cells) and turn state."""

    def __init__(self) -> None:
        self.board: List[str] = [EMPTY] * 9
        self.current_player: str = PLAYER_X
        self.winner: Optional[str] = None
        self.winning_line: Optional[List[int]] = None

    def available_moves(self) -> List[int]:
        return [i for i, cell in enumerate(self.board) if cell == EMPTY]

    def check_winner(self, board: Optional[List[str]] = None) -> Optional[str]:
        board = board if board is not None else self.board
        for a, b, c in WIN_LINES:
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]
        return None

    def winning_line_for(self, board: Optional[List[str]] = None) -> Optional[List[int]]:
        board = board if board is not None else self.board
        for line in WIN_LINES:
            a, b, c = line
            if board[a] and board[a] == board[b] == board[c]:
                return list(line)
        return None

    def is_draw(self, board: Optional[List[str]] = None) -> bool:
        board = board if board is not None else self.board
        return self.check_winner(board) is None and EMPTY not in board

    def is_over(self) -> bool:
        return self.winner is not None or self.is_draw()

    def make_move(self, position: int, player: str) -> None:
        if self.is_over():
            raise ValueError("Game is already over")
        if not 0 <= position < 9:
            raise ValueError("Position must be between 0 and 8")
        if self.board[position] != EMPTY:
            raise ValueError("Cell is already occupied")
        if player != self.current_player:
            raise ValueError(f"It is not {player}'s turn")

        self.board[position] = player
        self.winner = self.check_winner()
        self.winning_line = self.winning_line_for()
        self.current_player = PLAYER_O if player == PLAYER_X else PLAYER_X

    def best_move(self, player: str) -> int:
        """Return the optimal move for `player` using minimax with alpha-beta pruning."""
        opponent = PLAYER_O if player == PLAYER_X else PLAYER_X
        best_score = float("-inf")
        move = self.available_moves()[0]

        for pos in self.available_moves():
            board = self.board[:]
            board[pos] = player
            score = self._minimax(board, depth=1, is_maximizing=False,
                                   player=player, opponent=opponent,
                                   alpha=float("-inf"), beta=float("inf"))
            if score > best_score:
                best_score = score
                move = pos
        return move

    def _minimax(self, board, depth, is_maximizing, player, opponent, alpha, beta):
        winner = self.check_winner(board)
        if winner == player:
            return 10 - depth
        if winner == opponent:
            return depth - 10
        if EMPTY not in board:
            return 0

        moves = [i for i, cell in enumerate(board) if cell == EMPTY]

        if is_maximizing:
            best = float("-inf")
            for pos in moves:
                board[pos] = player
                best = max(best, self._minimax(board, depth + 1, False, player, opponent, alpha, beta))
                board[pos] = EMPTY
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = float("inf")
            for pos in moves:
                board[pos] = opponent
                best = min(best, self._minimax(board, depth + 1, True, player, opponent, alpha, beta))
                board[pos] = EMPTY
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    def to_dict(self) -> dict:
        return {
            "board": self.board,
            "current_player": self.current_player,
            "winner": self.winner,
            "winning_line": self.winning_line,
            "is_draw": self.is_draw(),
            "is_over": self.is_over(),
        }
