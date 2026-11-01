import { useState } from "react";

export default function SearchBar({ onSubmit, disabled }) {
  const [value, setValue] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    const query = value.trim();
    if (query) onSubmit(query);
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Enter a song name or paste a YouTube link..."
        disabled={disabled}
        aria-label="Song name or YouTube link"
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        {disabled ? "Working..." : "Get Piano Notes"}
      </button>
    </form>
  );
}
