import type { EventLogEntry, Pallet } from "../lib/types";
import type { RightPanelTab } from "../hooks/useRightPanelTab";

type Props = {
  tab: RightPanelTab;
  setTab: (tab: RightPanelTab) => void;
  pallets: Pallet[];
  events: EventLogEntry[];
};

export function RightPanel({ tab, setTab, pallets, events }: Props) {
  return (
    <aside className="w-[280px] shrink-0 border-l border-border-soft bg-white/40 flex flex-col">
      <div className="flex border-b border-border-soft">
        <TabButton label="Pallet Slots" active={tab === "pallets"} onClick={() => setTab("pallets")} />
        <TabButton label="Event Log" active={tab === "events"} onClick={() => setTab("events")} />
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === "pallets" ? <PalletsTab pallets={pallets} /> : <EventsTab events={events} />}
      </div>
    </aside>
  );
}

function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        "flex-1 text-xs py-3 tracking-wide " +
        (active
          ? "text-text-primary font-semibold border-b-2 border-accent -mb-px"
          : "text-text-secondary hover:text-text-primary")
      }
    >
      {label}
    </button>
  );
}

function PalletsTab({ pallets }: { pallets: Pallet[] }) {
  const robot1 = pallets.filter((p) => p.robot_id === 1);
  const robot2 = pallets.filter((p) => p.robot_id === 2);
  const activeCount = pallets.filter((p) => p.destination !== null).length;

  return (
    <div className="px-4 py-4 flex flex-col gap-4">
      <div className="text-[10px] tracking-widest text-text-secondary">
        {activeCount} ACTIVE SLOTS
      </div>

      <RobotSection label="ROBOT 1" pallets={robot1} />
      <RobotSection label="ROBOT 2" pallets={robot2} />
    </div>
  );
}

function RobotSection({ label, pallets }: { label: string; pallets: Pallet[] }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-[10px] tracking-widest text-text-secondary">{label}</div>
      {pallets.map((p) => (
        <PalletCard key={`${p.robot_id}-${p.slot_id}`} pallet={p} />
      ))}
    </div>
  );
}

function PalletCard({ pallet }: { pallet: Pallet }) {
  const awaiting = pallet.destination === null;
  return (
    <div className="border border-border-soft rounded-md px-3 py-2 bg-white/60 flex flex-col gap-2">
      <div className="flex justify-between items-center">
        <span className="font-bold text-sm text-text-primary">
          {pallet.slot_id.toString().padStart(2, "0")}
        </span>
        <span className="font-mono text-[11px] text-text-secondary">
          {awaiting ? "AWAITING DESTINATION" : pallet.destination}
        </span>
      </div>

      <div className="grid grid-cols-4 gap-1">
        {Array.from({ length: 12 }, (_, i) => (
          <div
            key={i}
            className={
              "h-3 rounded-[2px] " +
              (i < pallet.filled ? "bg-pallet-fill" : "bg-pallet-empty")
            }
          />
        ))}
      </div>

      <div className="flex justify-end">
        <span className="font-mono text-[10px] text-text-secondary">
          {pallet.filled}/{pallet.capacity}
        </span>
      </div>
    </div>
  );
}

function EventsTab({ events }: { events: EventLogEntry[] }) {
  return (
    <div className="px-4 py-4 flex flex-col gap-2">
      <div className="text-[10px] tracking-widest text-text-secondary mb-2">
        RECENT EVENTS
      </div>
      {events.length === 0 ? (
        <div className="text-text-secondary text-xs italic">
          No events yet. Start simulation to see activity.
        </div>
      ) : (
        events.slice(0, 50).map((ev, i) => <EventRow key={i} entry={ev} />)
      )}
    </div>
  );
}

function EventRow({ entry }: { entry: EventLogEntry }) {
  const ts = formatTimestamp(entry.t);
  const message = entry.message.replace(/\b(\d{14})(\d{6})\b/g, "…$2");
  return (
    <div className="flex items-baseline gap-2 text-[11px] py-1 border-b border-border-soft/50">
      <span className="font-mono text-text-secondary">{ts}</span>
      <span className="uppercase text-[9px] tracking-widest text-accent">
        {entry.type}
      </span>
      <span className="text-text-primary truncate">{message}</span>
    </div>
  );
}

function formatTimestamp(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return [h, m, s].map((n) => n.toString().padStart(2, "0")).join(":");
}
