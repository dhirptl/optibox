import type { Slot } from "../lib/types";

type Props = {
  slot: Slot | null;
  onClose: () => void;
};

export function BoxTooltip({ slot, onClose }: Props) {
  if (!slot || !slot.box) return null;
  const { box, position } = slot;
  const positionLabel =
    `Aisle ${position.aisle} / Side ${position.side.toString().padStart(2, "0")} ` +
    `/ X=${position.x} / Y=${position.y} / Z=${position.z}`;

  return (
    <div
      className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-lg border border-border-soft shadow-lg px-5 py-4 min-w-[340px]"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <span className="text-[10px] tracking-widest text-text-secondary">
          BOX
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="text-text-secondary hover:text-text-primary text-sm leading-none"
        >
          ×
        </button>
      </div>

      <div className="font-mono text-sm text-text-primary tracking-tight break-all mb-3">
        <span>{box.box_id.slice(0, 7)}</span>
        <span className="bg-pallet-empty text-accent font-semibold px-0.5 rounded-sm">
          {box.box_id.slice(7, 15)}
        </span>
        <span>{box.box_id.slice(15, 20)}</span>
      </div>

      <Row label="Destination" value={box.destination} mono />
      <Row label="Position" value={positionLabel} />
      <Row label="Loaded at" value="--:--:--" mono muted />
    </div>
  );
}

function Row({
  label,
  value,
  mono,
  muted,
}: {
  label: string;
  value: string;
  mono?: boolean;
  muted?: boolean;
}) {
  return (
    <div className="flex justify-between items-baseline gap-4 py-1 text-xs">
      <span className="text-text-secondary tracking-wide uppercase text-[10px]">
        {label}
      </span>
      <span
        className={
          (mono ? "font-mono " : "") +
          (muted ? "text-text-secondary" : "text-text-primary")
        }
      >
        {value}
      </span>
    </div>
  );
}
