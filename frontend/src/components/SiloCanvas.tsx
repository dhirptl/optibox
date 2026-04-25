import { useEffect, useMemo } from "react";
import { formatPositionString } from "../lib/parsing";
import type { SiloState, Slot } from "../lib/types";

type Props = {
  silo: SiloState;
  y: number;
  debugEnabled?: boolean;
  highlightedPositions?: Set<string>;
  shuttleXByAisle?: Record<number, number>;
  selectedShuttle: number | null;
  onSelectSlot: (slot: Slot) => void;
  onSelectShuttle: (id: number) => void;
  onClearSelection: () => void;
};

const AISLES = [1, 2, 3, 4] as const;
const X_RANGE = Array.from({ length: 60 }, (_, i) => i + 1);
const RULER_TICKS = [1, 10, 20, 30, 40, 50, 60];

const BOX_PX = 14;
const ROW_GAP_PX = 1;

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: `repeat(60, ${BOX_PX}px)`,
  columnGap: `${ROW_GAP_PX}px`,
};

export function SiloCanvas({
  silo,
  y,
  debugEnabled = false,
  highlightedPositions = new Set<string>(),
  shuttleXByAisle = {},
  selectedShuttle,
  onSelectSlot,
  onSelectShuttle,
  onClearSelection,
}: Props) {
  const visibleFilledSlots = useMemo(() => {
    if (!debugEnabled) return 0;
    let filled = 0;
    for (const aisle of AISLES) {
      for (const side of [1, 2] as const) {
        for (const x of X_RANGE) {
          for (const z of [1, 2] as const) {
            const key = formatPositionString({ aisle, side, x, y, z });
            if (silo.get(key)?.box) {
              filled += 1;
            }
          }
        }
      }
    }
    return filled;
  }, [debugEnabled, silo, y]);

  useEffect(() => {
    if (!debugEnabled) return;
    console.debug("[silo-canvas]", {
      y,
      visibleFilledSlots,
      highlightedSlotsThisTick: highlightedPositions.size,
    });
  }, [debugEnabled, highlightedPositions, visibleFilledSlots, y]);

  return (
    <div
      className="flex flex-col items-center gap-6 py-6"
      onClick={onClearSelection}
    >
      {AISLES.map((aisle) => (
        <AisleStrip
          key={aisle}
          aisle={aisle}
          y={y}
          silo={silo}
          highlightedPositions={highlightedPositions}
          shuttleX={shuttleXByAisle[aisle] ?? 0}
          shuttleSelected={selectedShuttle === aisle}
          onSelectSlot={onSelectSlot}
          onSelectShuttle={onSelectShuttle}
        />
      ))}
    </div>
  );
}

function AisleStrip({
  aisle,
  y,
  silo,
  highlightedPositions,
  shuttleX,
  shuttleSelected,
  onSelectSlot,
  onSelectShuttle,
}: {
  aisle: number;
  y: number;
  silo: SiloState;
  highlightedPositions: Set<string>;
  shuttleX: number;
  shuttleSelected: boolean;
  onSelectSlot: (slot: Slot) => void;
  onSelectShuttle: (id: number) => void;
}) {
  return (
    <div
      className="flex items-stretch gap-3"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="w-20 flex items-center justify-end">
        <span className="text-[10px] tracking-widest text-text-secondary font-mono">
          AISLE {aisle.toString().padStart(2, "0")}
        </span>
      </div>

      <div className="flex flex-col gap-1 bg-white/40 px-3 py-3 rounded-md border border-border-soft">
        <Row
          aisle={aisle}
          side={1}
          y={y}
          silo={silo}
          highlightedPositions={highlightedPositions}
          onSelectSlot={onSelectSlot}
        />
        <Corridor
          aisle={aisle}
          shuttleX={shuttleX}
          shuttleSelected={shuttleSelected}
          onSelectShuttle={onSelectShuttle}
        />
        <Row
          aisle={aisle}
          side={2}
          y={y}
          silo={silo}
          highlightedPositions={highlightedPositions}
          onSelectSlot={onSelectSlot}
        />
        <Ruler />
      </div>
    </div>
  );
}

function Row({
  aisle,
  side,
  y,
  silo,
  highlightedPositions,
  onSelectSlot,
}: {
  aisle: number;
  side: 1 | 2;
  y: number;
  silo: SiloState;
  highlightedPositions: Set<string>;
  onSelectSlot: (slot: Slot) => void;
}) {
  // Side 1 row: Z=2 on top (outer/wall), Z=1 on bottom (closer to corridor below).
  // Side 2 row: Z=1 on top (closer to corridor above), Z=2 on bottom (outer/wall).
  const topZ: 1 | 2 = side === 1 ? 2 : 1;
  const bottomZ: 1 | 2 = side === 1 ? 1 : 2;

  return (
    <div style={gridStyle}>
      {X_RANGE.map((x) => {
        const topKey = formatPositionString({ aisle, side, x, y, z: topZ });
        const bottomKey = formatPositionString({ aisle, side, x, y, z: bottomZ });
        const topSlot = silo.get(topKey);
        const bottomSlot = silo.get(bottomKey);
        return (
          <div
            key={x}
            className="flex flex-col"
            style={{ rowGap: `${ROW_GAP_PX}px` }}
          >
            <BoxSquare
              slot={topSlot}
              highlighted={highlightedPositions.has(topKey)}
              onSelectSlot={onSelectSlot}
            />
            <BoxSquare
              slot={bottomSlot}
              highlighted={highlightedPositions.has(bottomKey)}
              onSelectSlot={onSelectSlot}
            />
          </div>
        );
      })}
    </div>
  );
}

function BoxSquare({
  slot,
  highlighted,
  onSelectSlot,
}: {
  slot: Slot | undefined;
  highlighted: boolean;
  onSelectSlot: (slot: Slot) => void;
}) {
  const filled = slot?.box != null;
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        if (slot && slot.box) onSelectSlot(slot);
      }}
      disabled={!filled}
      style={{ width: `${BOX_PX}px`, height: `${BOX_PX}px` }}
      className={
        "rounded-[2px] " +
        (highlighted ? "ring-2 ring-accent/70 " : "") +
        (filled
          ? "bg-box-resting hover:bg-box-active transition-colors"
          : "border border-slot-empty bg-transparent cursor-default")
      }
      aria-label={filled ? `Box ${slot!.box!.box_id}` : "Empty slot"}
    />
  );
}

function Corridor({
  aisle,
  shuttleX,
  shuttleSelected,
  onSelectShuttle,
}: {
  aisle: number;
  shuttleX: number;
  shuttleSelected: boolean;
  onSelectShuttle: (id: number) => void;
}) {
  const normalizedX = Math.min(60, Math.max(0, shuttleX));
  const shuttleLeftPct = (normalizedX / 60) * 100;

  return (
    <div
      style={{ ...gridStyle, height: "10px" }}
      className="bg-pallet-empty rounded-[2px] relative"
    >
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onSelectShuttle(aisle);
        }}
        aria-label={`Shuttle aisle ${aisle}`}
        style={{
          position: "absolute",
          left: `${shuttleLeftPct}%`,
          top: "1px",
          width: "12px",
          height: "8px",
          transform: "translateX(-50%)",
        }}
        className={
          "bg-shuttle rounded-[2px] " +
          (shuttleSelected ? "outline outline-2 outline-accent" : "")
        }
      />
    </div>
  );
}

function Ruler() {
  return (
    <div
      style={gridStyle}
      className="text-[9px] font-mono text-text-secondary mt-1 select-none"
    >
      {RULER_TICKS.map((tick) => (
        <span
          key={tick}
          style={{ gridColumn: tick, gridRow: 1 }}
          className="text-center"
        >
          {tick}
        </span>
      ))}
    </div>
  );
}
