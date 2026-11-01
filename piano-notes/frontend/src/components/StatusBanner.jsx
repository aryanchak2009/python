const STAGE_LABELS = {
  pending: "Queuing...",
  downloading: "Downloading audio from YouTube...",
  transcribing: "Listening and transcribing piano notes (this can take a minute)...",
};

export default function StatusBanner({ job }) {
  if (!job) return null;

  if (job.status === "error") {
    return (
      <div className="status-banner status-error">
        <span className="status-dot" />
        {job.error || "Something went wrong."}
      </div>
    );
  }

  if (job.status === "done") return null;

  return (
    <div className="status-banner status-working">
      <span className="spinner" />
      {STAGE_LABELS[job.status] || "Working..."}
    </div>
  );
}
