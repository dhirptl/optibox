import { useState } from "react";
import { resetSilo } from "../lib/api";
import type { SimulationMetrics } from "../lib/types";

type Props = {
  onAfterReset: () => void;
  currentTick: number;
  totalTicks: number;
  finalMetrics: SimulationMetrics;
  activeSpeed: number;
  playing: boolean;
  controlsDisabled: boolean;
  onSelectSpeed: (speed: number) => void;
  onTogglePlay: () => void;
};

const SPEED_OPTIONS = [1, 2, 5, 10, 30] as const;

export function TopBar({
  onAfterReset,
  currentTick,
  totalTicks,
  finalMetrics,
  activeSpeed,
  playing,
  controlsDisabled,
  onSelectSpeed,
  onTogglePlay,
}: Props) {
  const [resetting, setResetting] = useState(false);
  const isFinalTick = totalTicks > 0 && currentTick >= totalTicks;
  const fullPalletsValue = isFinalTick
    ? `${finalMetrics.full_pallets_out_of_8} / 8`
    : "-- / 8";
  const palletsCompletedValue = isFinalTick
    ? String(finalMetrics.pallets_completed)
    : "--";
  const avgTimeValue = isFinalTick
    ? `${finalMetrics.avg_time_per_pallet.toFixed(2)}s`
    : "--s";

  async function handleReset() {
    setResetting(true);
    try {
      await resetSilo();
      onAfterReset();
    } catch {
      // Phase 1: surfaced via the offline banner; silently noop here.
    } finally {
      setResetting(false);
    }
  }

  return (
    <header className="bg-white/60 border-b border-border-soft pl-16 pr-8 py-4 flex items-center gap-8">
      <div className="flex flex-col leading-tight">
        <span className="font-sans font-bold tracking-wider text-text-primary text-xl">
          OPTIBOX
        </span>
        <span className="text-text-secondary text-xs">
          warehouse flow simulator
        </span>
      </div>

      <div className="flex items-center gap-10 ml-24 mt-3">
        <Metric label="FULL PALLETS" value={fullPalletsValue} />
        <Metric label="PALLETS COMPLETED" value={palletsCompletedValue} />
        <Metric label="AVG TIME / PALLET" value={avgTimeValue} />
      </div>

      <div className="ml-auto flex items-center gap-4">
        <span className="font-mono text-sm text-text-secondary tabular-nums">
          {`${formatHHMMSS(currentTick)} / ${formatHHMMSS(totalTicks)}`}
        </span>

        <div className="flex items-center gap-1">
          {SPEED_OPTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onSelectSpeed(s)}
              disabled={controlsDisabled}
              className={
                "px-2.5 py-1 rounded-full text-xs font-mono transition-colors " +
                (s === activeSpeed
                  ? "bg-accent text-white"
                  : "bg-pallet-empty text-text-secondary") +
                (controlsDisabled ? " opacity-50 cursor-not-allowed" : "")
              }
            >
              {s}×
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={onTogglePlay}
          disabled={controlsDisabled}
          className="px-3 py-1.5 rounded-full text-xs bg-pallet-empty text-text-secondary hover:bg-[#e2dbcd] disabled:opacity-50"
        >
          {playing ? "❚❚ Pause" : "▶ Play"}
        </button>

        <button
          type="button"
          onClick={handleReset}
          disabled={resetting}
          className="px-3 py-1.5 rounded-full text-xs border border-border-soft text-text-primary hover:bg-pallet-empty disabled:opacity-50"
        >
          {resetting ? "…" : "Reset"}
        </button>
      </div>
    </header>
  );
}

function formatHHMMSS(secondsRaw: number): string {
  const seconds = Math.max(0, Math.floor(secondsRaw));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return [h, m, s].map((value) => value.toString().padStart(2, "0")).join(":");
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col leading-none">
      <span className="text-[10px] tracking-widest text-text-secondary mb-1">
        {label}
      </span>
      <span
        className="font-sans font-semibold text-text-primary tabular-nums"
        style={{ fontSize: "36px" }}
      >
        {value}
      </span>
    </div>
  );
}
