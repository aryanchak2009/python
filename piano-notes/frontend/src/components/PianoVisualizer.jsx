import { useMemo, useRef } from "react";
import { buildKeyboardLayout } from "../pianoLayout";
import Keyboard from "./Keyboard.jsx";
import FallingNotes from "./FallingNotes.jsx";
import PlaybackBar from "./PlaybackBar.jsx";

const FALL_HEIGHT = 320;

export default function PianoVisualizer({ job }) {
  const audioRef = useRef(null);
  const stageRef = useRef(null);

  const layout = useMemo(() => {
    if (!job.notes || job.notes.length === 0) {
      return buildKeyboardLayout(48, 72);
    }
    const pitches = job.notes.map((n) => n.pitch);
    return buildKeyboardLayout(Math.min(...pitches), Math.max(...pitches));
  }, [job.notes]);

  return (
    <div className="visualizer">
      <audio ref={audioRef} src={job.audio_url} preload="auto" />
      <PlaybackBar audioRef={audioRef} duration={job.duration} title={job.title} />

      <div className="stage" ref={stageRef} style={{ width: layout.totalWidth }}>
        <FallingNotes
          notes={job.notes}
          layout={layout}
          audioRef={audioRef}
          containerRef={stageRef}
          height={FALL_HEIGHT}
        />
        <Keyboard layout={layout} />
      </div>

      <p className="note-count">{job.notes.length} notes transcribed</p>
    </div>
  );
}
