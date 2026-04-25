import { useState } from "react";
import { TopBar } from "./components/TopBar";
import { YLevelSelector } from "./components/YLevelSelector";
import { SiloCanvas } from "./components/SiloCanvas";
import { BoxTooltip } from "./components/BoxTooltip";
import { RightPanel } from "./components/RightPanel";
import { BottomBar } from "./components/BottomBar";
import { StartModal } from "./components/StartModal";
import { BackendOfflineBanner } from "./components/BackendOfflineBanner";
import { useSiloState } from "./hooks/useSiloState";
import { useYLevel } from "./hooks/useYLevel";
import { useSelectedBox } from "./hooks/useSelectedBox";
import { useSelectedShuttle } from "./hooks/useSelectedShuttle";
import { useRightPanelTab } from "./hooks/useRightPanelTab";
import { useBackendHealth } from "./hooks/useBackendHealth";
import type { EventLogEntry, Pallet } from "./lib/types";

const DEFAULT_PALLETS: Pallet[] = [
  ...[1, 2, 3, 4].map(
    (slot_id): Pallet => ({
      slot_id,
      robot_id: 1,
      destination: null,
      filled: 0,
      capacity: 12,
    }),
  ),
  ...[1, 2, 3, 4].map(
    (slot_id): Pallet => ({
      slot_id,
      robot_id: 2,
      destination: null,
      filled: 0,
      capacity: 12,
    }),
  ),
];

const PHASE_1_EVENTS: EventLogEntry[] = [];

export default function App() {
  const { silo, refetch } = useSiloState();
  const { y, setY } = useYLevel();
  const { selectedSlot, selectSlot, clearSelection: clearBox } = useSelectedBox();
  const { selectedShuttle, selectShuttle, clearShuttle } = useSelectedShuttle();
  const { tab, setTab } = useRightPanelTab();
  const healthy = useBackendHealth();
  const [startModalOpen, setStartModalOpen] = useState(true);

  function clearAllSelections() {
    clearBox();
    clearShuttle();
  }

  return (
    <div className="h-screen flex flex-col bg-bg-cream text-text-primary">
      <BackendOfflineBanner healthy={healthy} />
      <TopBar
        onAfterReset={() => {
          refetch();
          setStartModalOpen(true);
        }}
      />
      <YLevelSelector y={y} setY={setY} />

      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 overflow-auto">
          <SiloCanvas
            silo={silo}
            y={y}
            selectedShuttle={selectedShuttle}
            onSelectSlot={selectSlot}
            onSelectShuttle={selectShuttle}
            onClearSelection={clearAllSelections}
          />
        </main>
        <RightPanel
          tab={tab}
          setTab={setTab}
          pallets={DEFAULT_PALLETS}
          events={PHASE_1_EVENTS}
        />
      </div>

      <BottomBar />

      <BoxTooltip slot={selectedSlot} onClose={clearBox} />

      {startModalOpen && (
        <StartModal
          onClose={() => setStartModalOpen(false)}
          onAfterRandomize={refetch}
        />
      )}
    </div>
  );
}
