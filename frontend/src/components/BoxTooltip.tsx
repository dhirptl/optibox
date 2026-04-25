import { useEffect, useRef } from 'react'
import type { SelectedBoxState } from '../hooks/useSelectedBox'

interface BoxTooltipProps {
  selected: SelectedBoxState
  onClose: () => void
}

export function BoxTooltip({ selected, onClose }: BoxTooltipProps) {
  const ref = useRef<HTMLDivElement | null>(null)
  const { slot } = selected

  useEffect(() => {
    function onDocumentMouseDown(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) onClose()
    }
    window.addEventListener('mousedown', onDocumentMouseDown)
    return () => window.removeEventListener('mousedown', onDocumentMouseDown)
  }, [onClose])

  if (!slot.box) return null

  const id = slot.box.box_id
  const prefix = id.slice(0, 7)
  const destination = id.slice(7, 15)
  const suffix = id.slice(15)

  return (
    <div
      ref={ref}
      className="fixed z-30 w-[320px] rounded-xl bg-bg-white border border-border-soft shadow-lg p-4"
      style={{ left: selected.x + 10, top: selected.y + 10 }}
    >
      <button
        type="button"
        onClick={onClose}
        className="absolute top-2 right-2 text-text-secondary"
      >
        ×
      </button>
      <div className="font-mono text-sm break-all mb-3">
        {prefix}
        <span className="bg-pallet-empty rounded px-1">{destination}</span>
        {suffix}
      </div>
      <InfoRow label="Destination" value={slot.box.destination} mono />
      <InfoRow
        label="Position"
        value={`Aisle ${slot.position.aisle} / Side ${slot.position.side
          .toString()
          .padStart(2, '0')} / X=${slot.position.x} / Y=${slot.position.y} / Z=${slot.position.z}`}
      />
      <InfoRow label="Loaded at" value="--:--:--" mono />
    </div>
  )
}

function InfoRow({
  label,
  value,
  mono,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div className="text-sm mb-1.5">
      <span className="text-text-secondary mr-2">{label}:</span>
      <span className={mono ? 'font-mono' : ''}>{value}</span>
    </div>
  )
}
