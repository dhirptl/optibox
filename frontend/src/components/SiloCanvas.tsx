import { formatPositionString } from '../lib/parsing'
import type { Slot, SiloState } from '../lib/types'
import type { SelectedShuttle } from '../hooks/useSelectedShuttle'

interface SiloCanvasProps {
  silo: SiloState
  y: number
  selectedShuttle: SelectedShuttle | null
  onSelectBox: (slot: Slot, x: number, y: number) => void
  onSelectShuttle: (shuttle: SelectedShuttle) => void
  onClearSelection: () => void
}

const X_TICKS = [0, 10, 20, 30, 40, 50, 60]

export function SiloCanvas({
  silo,
  y,
  selectedShuttle,
  onSelectBox,
  onSelectShuttle,
  onClearSelection,
}: SiloCanvasProps) {
  return (
    <section
      className="h-full overflow-auto p-6"
      onClick={() => onClearSelection()}
      role="presentation"
    >
      <div className="mx-auto max-w-[1240px] space-y-6">
        {Array.from({ length: 4 }, (_, i) => i + 1).map((aisle) => (
          <AisleStrip
            key={aisle}
            aisle={aisle}
            y={y}
            silo={silo}
            selectedShuttle={selectedShuttle}
            onSelectBox={onSelectBox}
            onSelectShuttle={onSelectShuttle}
          />
        ))}
      </div>
    </section>
  )
}

function AisleStrip({
  aisle,
  y,
  silo,
  selectedShuttle,
  onSelectBox,
  onSelectShuttle,
}: {
  aisle: number
  y: number
  silo: SiloState
  selectedShuttle: SelectedShuttle | null
  onSelectBox: (slot: Slot, x: number, y: number) => void
  onSelectShuttle: (shuttle: SelectedShuttle) => void
}) {
  const shuttleX = 0
  const selected =
    selectedShuttle?.aisle === aisle && selectedShuttle?.y === y

  return (
    <div className="grid grid-cols-[88px_1fr] items-center gap-3">
      <div className="text-[11px] font-medium tracking-ui text-text-secondary">
        AISLE {aisle.toString().padStart(2, '0')}
      </div>

      <div className="rounded-xl border border-border-soft bg-bg-white p-3">
        <SlotRow aisle={aisle} side={1} y={y} silo={silo} onSelectBox={onSelectBox} />
        <div className="h-5 bg-slot-empty rounded mt-1 mb-1 relative">
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation()
              onSelectShuttle({ aisle, y, current_x: shuttleX })
            }}
            className={`absolute top-1/2 -translate-y-1/2 h-2 w-3 rounded-sm ${
              selected ? 'bg-box-active ring-2 ring-box-active/30' : 'bg-shuttle'
            }`}
            style={{ left: `calc(${(shuttleX / 60) * 100}% + 2px)` }}
          />
        </div>
        <SlotRow aisle={aisle} side={2} y={y} silo={silo} onSelectBox={onSelectBox} />

        <div className="relative h-5 mt-2">
          {X_TICKS.map((x) => (
            <div
              key={x}
              className="absolute -translate-x-1/2 text-[10px] font-mono text-text-secondary"
              style={{ left: `${(x / 60) * 100}%` }}
            >
              X={x}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function SlotRow({
  aisle,
  side,
  y,
  silo,
  onSelectBox,
}: {
  aisle: number
  side: 1 | 2
  y: number
  silo: SiloState
  onSelectBox: (slot: Slot, x: number, y: number) => void
}) {
  return (
    <div
      className="grid gap-x-[2px]"
      style={{ gridTemplateColumns: 'repeat(60, minmax(0, 1fr))' }}
    >
      {Array.from({ length: 60 }, (_, index) => index + 1).map((x) => {
        const zOrder: (1 | 2)[] = side === 1 ? [2, 1] : [1, 2]
        return (
          <div key={`${side}-${x}`} className="flex gap-[1px]">
            {zOrder.map((z) => {
              const code = formatPositionString({ aisle, side, x, y, z })
              const slot = silo.get(code) ?? {
                position: { aisle, side, x, y, z },
                box: null,
              }
              return (
                <button
                  key={code}
                  type="button"
                  className={`h-3 w-3 rounded-[2px] border ${
                    slot.box
                      ? 'bg-box-resting border-box-resting'
                      : 'bg-transparent border-slot-empty'
                  }`}
                  onClick={(event) => {
                    event.stopPropagation()
                    onSelectBox(slot, event.clientX, event.clientY)
                  }}
                />
              )
            })}
          </div>
        )
      })}
    </div>
  )
}
