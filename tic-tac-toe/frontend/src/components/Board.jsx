import Square from "./Square.jsx";

export default function Board({ board, winningLine, onPlay, disabled }) {
  return (
    <div className="board">
      {board.map((value, index) => (
        <Square
          key={index}
          value={value}
          disabled={disabled}
          isWinning={Boolean(winningLine?.includes(index))}
          onClick={() => onPlay(index)}
        />
      ))}
    </div>
  );
}
