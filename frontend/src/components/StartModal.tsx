import { useState } from "react";
import { randomizeSilo } from "../lib/api";

type Props = {
  onClose: () => void;
  onAfterRandomize: () => void;
};

export function StartModal({ onClose, onAfterRandomize }: Props) {
  const [numBoxes, setNumBoxes] = useState(2500);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [didRandomize, setDidRandomize] = useState(false);

  async function handleRandomize() {
    setLoading(true);
    setError(null);
    try {
      await randomizeSilo(numBoxes);
      setDidRandomize(true);
      onAfterRandomize();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 bg-black/30 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl border border-border-soft shadow-xl px-8 py-7 w-[440px]"
        onClick={(e) => e.stopPropagation()}
      >
        <h1 className="text-3xl font-bold tracking-wide text-text-primary text-center">
          OPTIBOX
        </h1>
        <p className="text-center text-sm text-text-secondary mt-1">
          Warehouse Flow Simulator
        </p>

        <p className="text-center text-xs text-text-secondary mt-4 font-mono">
          1,000 boxes per hour. 32 shuttles. 8 pallet slots.
        </p>

        <div className="mt-6">
          <label
            htmlFor="num-boxes"
            className="text-xs tracking-wide text-text-secondary uppercase"
          >
            How many boxes to populate the silo?
          </label>
          <input
            id="num-boxes"
            type="number"
            min={0}
            max={7680}
            value={numBoxes}
            onChange={(e) => setNumBoxes(Number(e.target.value))}
            className="mt-2 w-full px-3 py-2 rounded-md border border-border-soft font-mono text-text-primary focus:outline-none focus:border-accent"
          />
          <p className="text-[11px] text-text-secondary mt-1">
            Try 1000–4000 for best visualization
          </p>
        </div>

        {error && (
          <p className="mt-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {error}
          </p>
        )}

        {didRandomize && !error && (
          <p className="mt-3 text-xs text-text-secondary italic">
            Silo populated. Re-roll or click outside to view.
          </p>
        )}

        <div className="mt-6 flex flex-col gap-2">
          <button
            type="button"
            onClick={handleRandomize}
            disabled={loading}
            className="w-full px-4 py-2.5 rounded-md bg-accent text-white text-sm hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Randomizing…" : "Randomize Silo"}
          </button>
          <button
            type="button"
            disabled
            className="w-full px-4 py-2.5 rounded-md bg-pallet-empty text-text-secondary text-sm opacity-50 cursor-not-allowed"
          >
            Start Simulation
          </button>
        </div>
      </div>
    </div>
  );
}
