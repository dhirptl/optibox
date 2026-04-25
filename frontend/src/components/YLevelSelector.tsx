type Props = {
  y: number;
  setY: (y: number) => void;
  unlockAllLevels?: boolean;
};

const Y_LEVELS = [1, 2, 3, 4, 5, 6, 7, 8] as const;

export function YLevelSelector({
  y,
  setY,
  unlockAllLevels = false,
}: Props) {
  return (
    <div className="flex items-center justify-center gap-3 py-3 border-b border-border-soft">
      <span className="text-[10px] tracking-widest text-text-secondary">
        VIEWING LEVEL
      </span>
      <div className="flex items-center gap-1">
        {Y_LEVELS.map((level) => {
          const active = level === y;
          const enabled = unlockAllLevels || level === 1;
          return (
            <button
              key={level}
              type="button"
              disabled={!enabled}
              onClick={() => enabled && setY(level)}
              title={
                enabled
                  ? undefined
                  : "Visualization limited to Y=1 for demo clarity"
              }
              className={
                "min-w-[44px] px-2 py-1 rounded-full text-xs font-mono " +
                (active
                  ? "bg-accent text-white"
                  : "bg-pallet-empty text-text-secondary") +
                (enabled
                  ? " hover:opacity-90 cursor-pointer"
                  : " opacity-40 cursor-not-allowed")
              }
            >
              {`Y=${level}`}
            </button>
          );
        })}
      </div>
    </div>
  );
}
