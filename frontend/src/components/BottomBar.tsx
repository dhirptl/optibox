import { useMemo, useRef, useState } from 'react'
import type { MouseEvent } from 'react'

interface BottomBarProps {
  disabled?: boolean
}

export function BottomBar({ disabled = true }: BottomBarProps) {
  const [progress, setProgress] = useState(0)
  const trackRef = useRef<HTMLDivElement | null>(null)
  const dragging = useRef(false)

  const filledWidth = useMemo(() => `${progress * 100}%`, [progress])

  function updateFromEvent(clientX: number) {
    if (disabled || !trackRef.current) return
    const rect = trackRef.current.getBoundingClientRect()
    const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
    setProgress(ratio)
  }

  function onMouseDown(event: MouseEvent<HTMLDivElement>) {
    if (disabled) return
    dragging.current = true
    updateFromEvent(event.clientX)
  }

  function onMouseMove(event: MouseEvent<HTMLDivElement>) {
    if (!dragging.current) return
    updateFromEvent(event.clientX)
  }

  function onMouseUp() {
    dragging.current = false
  }

  return (
    <footer className="h-[80px] bg-bg-white border-t border-border-soft px-6 flex items-center justify-between gap-8">
      <div className="w-[60%] flex items-center gap-3">
        <span className="h-2.5 w-2.5 rounded-full bg-status-green animate-pulse" />
        <span className="font-mono text-[20px] text-text-primary whitespace-nowrap overflow-hidden text-ellipsis">
          Awaiting simulation start...
        </span>
      </div>
      <div className="w-[40%] flex items-center gap-3">
        <div
          ref={trackRef}
          role="presentation"
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
          className={`relative h-6 flex-1 ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <div className="absolute top-1/2 left-0 h-1.5 w-full -translate-y-1/2 rounded-full bg-pallet-empty" />
          <div
            className={`absolute top-1/2 left-0 h-1.5 -translate-y-1/2 rounded-full ${
              disabled ? 'bg-border-soft' : 'bg-accent'
            }`}
            style={{ width: filledWidth }}
          />
          <div
            className={`absolute top-1/2 h-4 w-4 -translate-y-1/2 -translate-x-1/2 rounded-full border border-border-soft ${
              disabled ? 'bg-slot-empty' : 'bg-bg-white'
            }`}
            style={{ left: filledWidth }}
          />
        </div>
        <span className="font-mono text-sm text-text-secondary">
          {disabled ? '— / 10:00' : `${formatTime(progress * 600)} / 10:00`}
        </span>
      </div>
    </footer>
  )
}

function formatTime(secondsTotal: number) {
  const seconds = Math.floor(secondsTotal)
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}
