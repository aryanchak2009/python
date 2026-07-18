export default function Square({ value, onClick, disabled, isWinning }) {
  return (
    <button
      className={`square${isWinning ? " square--winning" : ""}`}
      onClick={onClick}
      disabled={disabled || Boolean(value)}
      aria-label={value ? `Cell filled with ${value}` : "Empty cell"}
    >
      {value}
    </button>
  );
}
