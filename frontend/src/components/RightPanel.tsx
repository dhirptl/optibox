import type { ReactNode } from 'react'
import type { EventLogEntry, PalletSlot, RightPanelTab } from '../lib/types'

interface RightPanelProps {
  tab: RightPanelTab
  setTab: (tab: RightPanelTab) => void
  palletSlots: PalletSlot[]
  events: EventLogEntry[]
}

export function RightPanel({ tab, setTab, palletSlots, events }: RightPanelProps) {
  return (
    <aside className="w-[280px] shrink-0 bg-bg-white border-l border-border-soft h-full flex flex-col">
      <div className="h-10 border-b border-border-soft grid grid-cols-2">
        <TabButton active={tab === 'pallets'} onClick={() => setTab('pallets')}>
          Pallet Slots
        </TabButton>
        <TabButton active={tab === 'events'} onClick={() => setTab('events')}>
          Event Log
        </TabButton>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {tab === 'pallets' ? (
          <PalletSlotsTab palletSlots={palletSlots} />
        ) : (
          <EventLogTab events={events} />
        )}
      </div>
    </aside>
  )
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`text-sm ${
        active
          ? 'text-text-primary border-b-2 border-accent'
          : 'text-text-secondary border-b-2 border-transparent'
      }`}
    >
      {children}
    </button>
  )
}

function PalletSlotsTab({ palletSlots }: { palletSlots: PalletSlot[] }) {
  const robot1 = palletSlots.filter((slot) => slot.robot_id === 1)
  const robot2 = palletSlots.filter((slot) => slot.robot_id === 2)
  return (
    <div>
      <p className="text-[10px] uppercase tracking-ui text-text-secondary mb-3">
        8 active slots
      </p>
      <RobotSection title="Robot 1" slots={robot1} />
      <RobotSection title="Robot 2" slots={robot2} />
    </div>
  )
}

function RobotSection({ title, slots }: { title: string; slots: PalletSlot[] }) {
  return (
    <section className="mb-4">
      <p className="text-[10px] uppercase tracking-ui text-text-secondary mb-2">
        {title}
      </p>
      <div className="space-y-2">
        {slots.map((slot) => (
          <article
            key={slot.slot_id}
            className="border border-border-soft rounded-lg p-2.5 bg-bg-white"
          >
            <div className="flex justify-between items-center mb-2">
              <strong>{slot.slot_id.toString().padStart(2, '0')}</strong>
              <span className="font-mono text-xs text-text-secondary italic">
                {slot.destination ?? 'AWAITING DESTINATION'}
              </span>
            </div>
            <div className="grid grid-cols-4 gap-1 mb-2">
              {Array.from({ length: 12 }, (_, i) => (
                <div
                  key={i}
                  className={`h-3 w-3 rounded-[2px] ${
                    i < slot.filled ? 'bg-pallet-fill' : 'bg-pallet-empty'
                  }`}
                />
              ))}
            </div>
            <div className="text-right text-xs text-text-secondary">
              {slot.filled}/{slot.capacity}
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

function EventLogTab({ events }: { events: EventLogEntry[] }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-ui text-text-secondary mb-3">
        Recent events
      </p>
      {events.length === 0 ? (
        <p className="text-sm text-text-secondary">
          No events yet. Start simulation to see activity.
        </p>
      ) : (
        <ul className="space-y-2">
          {events.slice(0, 50).map((event, idx) => (
            <li key={idx} className="text-sm border-b border-slot-empty pb-2">
              <div className="font-mono text-xs text-text-secondary">
                {formatTime(event.t)}
              </div>
              <div className="text-[10px] uppercase tracking-ui text-text-secondary">
                {event.type}
              </div>
              <div>{event.message}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function formatTime(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `00:${mins.toString().padStart(2, '0')}:${secs
    .toString()
    .padStart(2, '0')}`
}
