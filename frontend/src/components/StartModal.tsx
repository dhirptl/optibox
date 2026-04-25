import { useState } from 'react'

interface StartModalProps {
  loading: boolean
  error: string | null
  backendHealthy: boolean
  hasRandomized: boolean
  onRandomize: (numBoxes: number) => Promise<void>
  onUseMockData: () => Promise<void>
}

export function StartModal({
  loading,
  error,
  backendHealthy,
  hasRandomized,
  onRandomize,
  onUseMockData,
}: StartModalProps) {
  const [numBoxes, setNumBoxes] = useState(2500)

  return (
    <div className="fixed inset-0 z-40 bg-[#2A252033] flex items-center justify-center p-4">
      <div className="w-full max-w-[480px] rounded-2xl bg-bg-white border border-border-soft p-8 shadow-xl">
        <h2 className="m-0 text-4xl font-bold tracking-[0.08em]">OPTIBOX</h2>
        <p className="mt-1 text-lg">Warehouse Flow Simulator</p>
        <p className="text-sm text-text-secondary mt-2">
          1,000 boxes per hour. 32 shuttles. 8 pallet slots.
        </p>

        <label className="block mt-6 text-sm font-medium">
          How many boxes to populate the silo?
          <input
            type="number"
            min={0}
            max={7680}
            value={numBoxes}
            onChange={(event) => setNumBoxes(Number(event.target.value))}
            className="mt-2 w-full h-11 rounded-lg border border-border-soft px-3 text-base"
          />
        </label>
        <p className="text-xs text-text-secondary mt-1">
          Try 1000-4000 for best visualization
        </p>

        <button
          type="button"
          disabled={loading}
          onClick={() => void onRandomize(numBoxes)}
          className="mt-5 w-full h-11 rounded-full bg-accent text-white font-medium disabled:opacity-60"
        >
          {hasRandomized ? 'Generate Again' : '🎲 Randomize Silo'}
        </button>
        {!backendHealthy && (
          <button
            type="button"
            disabled={loading}
            onClick={() => void onUseMockData()}
            className="mt-2 w-full h-11 rounded-full border border-border-soft text-text-primary disabled:opacity-60"
          >
            Use mock data
          </button>
        )}
        <button
          type="button"
          disabled
          className="mt-2 w-full h-11 rounded-full border border-border-soft text-text-secondary opacity-60"
        >
          ▶ Start Simulation
        </button>

        {error && <p className="mt-3 text-sm text-red-700">{error}</p>}
      </div>
    </div>
  )
}
