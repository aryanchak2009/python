import { useEffect, useRef } from "react";

const LOOKAHEAD_SECONDS = 3.2;

// Renders the falling note bars on a <canvas> and highlights the matching
// piano keys, all driven by a requestAnimationFrame loop that reads the
// audio element's currentTime directly. Deliberately avoids React state for
// per-frame updates (60fps) -- it mutates the canvas and key DOM nodes
// in place instead.
export default function FallingNotes({ notes, layout, audioRef, containerRef, height }) {
  const canvasRef = useRef(null);
  const activeMidiRef = useRef(new Set());

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    let rafId;
    const dpr = window.devicePixelRatio || 1;

    function resize() {
      canvas.width = layout.totalWidth * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${layout.totalWidth}px`;
      canvas.style.height = `${height}px`;
    }
    resize();

    const ctx = canvas.getContext("2d");
    const pxPerSecond = height / LOOKAHEAD_SECONDS;
    const keyByMidi = new Map(layout.keys.map((key) => [key.midi, key]));

    function draw() {
      const audio = audioRef.current;
      const currentTime = audio ? audio.currentTime : 0;

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, layout.totalWidth, height);

      const stillActive = new Set();

      for (const note of notes) {
        const timeToStart = note.start - currentTime;
        const timeToEnd = note.end - currentTime;
        if (timeToEnd < -0.05 || timeToStart > LOOKAHEAD_SECONDS) continue;

        const key = keyByMidi.get(note.pitch);
        if (!key) continue;

        const top = Math.max(0, height - timeToEnd * pxPerSecond);
        const bottom = height - timeToStart * pxPerSecond;
        const barHeight = Math.max(4, bottom - top);

        ctx.fillStyle = key.color;
        ctx.globalAlpha = 0.35 + note.velocity * 0.65;
        const radius = Math.min(6, key.width / 2.2);
        roundedRect(ctx, key.left + 1, top, Math.max(2, key.width - 2), barHeight, radius);
        ctx.fill();

        if (currentTime >= note.start && currentTime <= note.end) {
          stillActive.add(note.pitch);
        }
      }
      ctx.restore();

      syncActiveKeys(container, activeMidiRef.current, stillActive);
      activeMidiRef.current = stillActive;

      rafId = requestAnimationFrame(draw);
    }

    rafId = requestAnimationFrame(draw);
    window.addEventListener("resize", resize);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", resize);
      syncActiveKeys(container, activeMidiRef.current, new Set());
    };
  }, [notes, layout, audioRef, containerRef, height]);

  return <canvas ref={canvasRef} className="falling-notes-canvas" />;
}

function syncActiveKeys(container, previous, current) {
  for (const midi of previous) {
    if (!current.has(midi)) {
      const el = container.querySelector(`[data-midi="${midi}"]`);
      if (el) el.classList.remove("active");
    }
  }
  for (const midi of current) {
    if (!previous.has(midi)) {
      const el = container.querySelector(`[data-midi="${midi}"]`);
      if (el) el.classList.add("active");
    }
  }
}

function roundedRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + width, y, radius);
  ctx.closePath();
}
