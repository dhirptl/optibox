import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  actionMessage?: string;
  currentTick?: number;
  totalTicks?: number;
  onSeek?: (tick: number) => void;
  scrubDisabled?: boolean;
};

export function BottomBar({
  actionMessage = "Awaiting simulation start...",
  currentTick = 0,
  totalTicks = 3600,
  onSeek,
  scrubDisabled = true,
}: Props) {
  return (
    <div className="border-t border-border-soft bg-white/40 px-6 py-4 flex items-center gap-6 min-h-[80px]">
      <div className="flex items-center gap-3 flex-[3]">
        <span className="w-2.5 h-2.5 rounded-full bg-status-green animate-pulse shrink-0" />
        <span
          className="text-text-primary truncate"
          style={{ fontFamily: "Georgia, serif", fontSize: "18px" }}
        >
          {actionMessage}
        </span>
      </div>

      <div className="flex items-center gap-3 flex-[2]">
        <ScrubBar
          current={currentTick}
          total={totalTicks}
          disabled={scrubDisabled}
          onSeek={onSeek}
        />
        <span className="font-mono text-xs text-text-secondary tabular-nums">
          {scrubDisabled ? "— / —" : `${formatHHMMSS(currentTick)} / ${formatHHMMSS(totalTicks)}`}
        </span>
      </div>
    </div>
  );
}

function ScrubBar({
  current,
  total,
  disabled,
  onSeek,
}: {
  current: number;
  total: number;
  disabled: boolean;
  onSeek?: (tick: number) => void;
}) {
  const trackRef = useRef<HTMLDivElement | null>(null);
  const [dragging, setDragging] = useState(false);
  const pct = total > 0 ? Math.min(100, Math.max(0, (current / total) * 100)) : 0;

  const seekFromEvent = useCallback(
    (clientX: number) => {
      if (disabled || !onSeek || !trackRef.current) return;
      const rect = trackRef.current.getBoundingClientRect();
      const ratio = (clientX - rect.left) / rect.width;
      const clamped = Math.min(1, Math.max(0, ratio));
      onSeek(clamped * total);
    },
    [disabled, onSeek, total],
  );

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: MouseEvent) => seekFromEvent(e.clientX);
    const onUp = () => setDragging(false);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [dragging, seekFromEvent]);

  return (
    <div
      ref={trackRef}
      onMouseDown={(e) => {
        if (disabled) return;
        seekFromEvent(e.clientX);
        setDragging(true);
      }}
      className={
        "flex-1 h-1.5 rounded-full bg-pallet-empty relative " +
        (disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer")
      }
    >
      <div
        className="absolute top-0 left-0 h-full rounded-full bg-accent"
        style={{ width: `${pct}%` }}
      />
      <div
        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-accent shadow-sm"
        style={{ left: `${pct}%` }}
      />
    </div>
  );
}

function formatHHMMSS(secondsRaw: number): string {
  const seconds = Math.max(0, Math.floor(secondsRaw));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map((value) => value.toString().padStart(2, "0")).join(":");
}
