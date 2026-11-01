import { useEffect, useRef, useState } from "react";
import SearchBar from "./components/SearchBar.jsx";
import StatusBanner from "./components/StatusBanner.jsx";
import PianoVisualizer from "./components/PianoVisualizer.jsx";
import { createSongJob, getSongJob } from "./api.js";

const POLL_INTERVAL_MS = 1200;

export default function App() {
  const [job, setJob] = useState(null);
  const pollRef = useRef(null);

  useEffect(() => () => clearInterval(pollRef.current), []);

  async function handleSearch(query) {
    clearInterval(pollRef.current);
    try {
      const created = await createSongJob(query);
      setJob(created);
      pollRef.current = setInterval(async () => {
        try {
          const updated = await getSongJob(created.job_id);
          setJob(updated);
          if (updated.status === "done" || updated.status === "error") {
            clearInterval(pollRef.current);
          }
        } catch (err) {
          setJob({ status: "error", error: err.message });
          clearInterval(pollRef.current);
        }
      }, POLL_INTERVAL_MS);
    } catch (err) {
      setJob({ status: "error", error: err.message });
    }
  }

  const isWorking = job && job.status !== "done" && job.status !== "error";

  return (
    <div className="app">
      <div className="backdrop" />
      <header>
        <h1>
          <span className="title-accent">Piano</span> Notes
        </h1>
        <p className="subtitle">
          Type a song name or paste a YouTube link. We'll find the audio, listen to it, and play it
          back on a virtual piano.
        </p>
      </header>

      <SearchBar onSubmit={handleSearch} disabled={isWorking} />
      <StatusBanner job={job} />

      {job && job.status === "done" && <PianoVisualizer job={job} />}
    </div>
  );
}
