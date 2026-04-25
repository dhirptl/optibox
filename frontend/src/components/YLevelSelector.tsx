interface YLevelSelectorProps {
  y: number
  setY: (level: number) => void
}

export function YLevelSelector({ y, setY }: YLevelSelectorProps) {
  return (
    <section className="h-[50px] bg-bg-white border-b border-border-soft flex items-center justify-center gap-6">
      <span className="text-[10px] uppercase tracking-ui text-text-secondary">
        Viewing level
      </span>
      <div className="flex gap-2">
        {Array.from({ length: 8 }, (_, index) => index + 1).map((level) => {
          const active = level === y
          return (
            <button
              key={level}
              type="button"
              onClick={() => setY(level)}
              className={`h-8 px-3 rounded-full text-xs font-medium ${
                active
                  ? 'bg-accent text-white'
                  : 'bg-pallet-empty text-text-secondary'
              }`}
            >
              Y={level}
            </button>
          )
        })}
      </div>
    </section>
  )
}
