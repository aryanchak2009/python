export default function Keyboard({ layout }) {
  const whiteKeys = layout.keys.filter((k) => k.white);
  const blackKeys = layout.keys.filter((k) => !k.white);

  return (
    <div className="keyboard" style={{ width: layout.totalWidth }}>
      {whiteKeys.map((key) => (
        <div
          key={key.midi}
          data-midi={key.midi}
          className="key key-white"
          style={{ left: key.left, width: key.width, "--key-color": key.color }}
        >
          <span className="key-label">{key.name.replace(/[0-9-]/g, "") === "C" ? key.name : ""}</span>
        </div>
      ))}
      {blackKeys.map((key) => (
        <div
          key={key.midi}
          data-midi={key.midi}
          className="key key-black"
          style={{ left: key.left, width: key.width, "--key-color": key.color }}
        />
      ))}
    </div>
  );
}
