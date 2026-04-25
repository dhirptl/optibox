interface TopBarProps {
  onReset: () => Promise<void> | void
  resetLoading?: boolean
}

const SPEEDS = ['1×', '2×', '5×', '10×', '30×']

export function TopBar({ onReset, resetLoading = false }: TopBarProps) {
  return (
    <header className="h-[70px] bg-bg-white border-b border-border-soft px-6 flex items-center justify-between gap-6">
      <div className="min-w-[220px]">
        <h1 className="m-0 text-[20px] font-bold tracking-[0.08em] leading-tight">
          OPTIBOX
        </h1>
        <p className="m-0 text-[10px] uppercase tracking-ui text-text-secondary">
          warehouse flow simulator
        </p>
      </div>

      <div className="flex-1 flex items-end justify-center gap-10">
        <Metric value="0%" label="FULL PALLETS" />
        <Metric value="0" label="PALLETS COMPLETED" />
        <Metric value="--" label="AVG TIME / PALLET" />
      </div>

      <div className="flex items-center gap-2 min-w-[390px] justify-end">
        <span className="font-mono text-[14px] text-text-primary mr-2">
          00:00:00 / 10:00:00
        </span>

        {SPEEDS.map((speed, index) => (
          <button
            key={speed}
            type="button"
            disabled
            className={`px-2.5 h-7 rounded-full text-xs border border-border-soft ${
              index === 0
                ? 'bg-accent text-white opacity-60'
                : 'bg-pallet-empty text-text-secondary opacity-60'
            }`}
          >
            {speed}
          </button>
        ))}

        <button
          type="button"
          disabled
          className="h-9 w-9 rounded-full bg-accent text-white opacity-60"
        >
          ▶
        </button>
        <button
          type="button"
          onClick={() => void onReset()}
          disabled={resetLoading}
          className="h-9 px-4 rounded-full border border-border-soft bg-bg-white text-[12px] disabled:opacity-50"
        >
          Reset
        </button>
      </div>
    </header>
  )
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center">
      <div className="text-[36px] leading-none font-semibold">{value}</div>
      <div className="mt-1 text-[10px] uppercase tracking-ui text-text-secondary">
        {label}
      </div>
    </div>
  )
}
