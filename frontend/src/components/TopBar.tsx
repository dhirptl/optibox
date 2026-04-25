import { useState } from "react";
import { resetSilo } from "../lib/api";

type Props = {
  onAfterReset: () => void;
};

const SPEED_OPTIONS = [1, 2, 5, 10, 30] as const;

export function TopBar({ onAfterReset }: Props) {
  const [activeSpeed] = useState<number>(1);
  const [resetting, setResetting] = useState(false);

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
        <Metric label="FULL PALLETS" value="—%" />
        <Metric label="PALLETS COMPLETED" value="—" />
        <Metric label="AVG TIME / PALLET" value="—" />
      </div>

      <div className="ml-auto flex items-center gap-4">
        <span className="font-mono text-sm text-text-secondary tabular-nums">
          00:00:00 / 10:00:00
        </span>

        <div className="flex items-center gap-1">
          {SPEED_OPTIONS.map((s) => (
            <button
              key={s}
              type="button"
              disabled
              className={
                "px-2.5 py-1 rounded-full text-xs font-mono transition-colors " +
                (s === activeSpeed
                  ? "bg-accent text-white"
                  : "bg-pallet-empty text-text-secondary") +
                " opacity-50 cursor-not-allowed"
              }
            >
              {s}×
            </button>
          ))}
        </div>

        <button
          type="button"
          disabled
          className="px-3 py-1.5 rounded-full text-xs bg-pallet-empty text-text-secondary opacity-50 cursor-not-allowed"
        >
          ▶ Play
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
