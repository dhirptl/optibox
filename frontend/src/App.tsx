import { useEffect, useState } from "react";
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
import { useSimulationPlayback } from "./hooks/useSimulationPlayback";
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
  const { silo, error: siloError, refetch } = useSiloState();
  const { y, setY } = useYLevel();
  const { selectedSlot, selectSlot, clearSelection: clearBox } = useSelectedBox();
  const { selectedShuttle, selectShuttle, clearShuttle } = useSelectedShuttle();
  const { tab, setTab } = useRightPanelTab();
  const healthy = useBackendHealth();
  const playback = useSimulationPlayback(y);
  const [startModalOpen, setStartModalOpen] = useState(true);

  function clearAllSelections() {
    clearBox();
    clearShuttle();
  }

  async function handleStartSimulation(numBoxes: number) {
    const ok = await playback.startSimulation({
      ticks: 3600,
      inboundSeed: 42,
      numBoxes,
      baseSilo: silo,
    });
    if (ok) {
      setStartModalOpen(false);
    }
  }

  const activePallets: Pallet[] = playback.hasSimulation
    ? playback.pallets
    : DEFAULT_PALLETS;
  const activeEvents: EventLogEntry[] = playback.hasSimulation
    ? playback.events
    : PHASE_1_EVENTS;
  const activeSilo = playback.hasSimulation ? playback.playbackSilo : silo;

  useEffect(() => {
    if (!import.meta.env.DEV || silo.size === 0) return;
    // Dev-only sanity probe for the CSV pipeline.
    console.debug("Silo loaded", {
      size: silo.size,
      sample01010010401: silo.get("01010010401")?.box?.box_id ?? null,
    });
  }, [silo]);

  return (
    <div className="h-screen flex flex-col bg-bg-cream text-text-primary">
      <BackendOfflineBanner healthy={healthy} />
      {siloError && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2 text-xs text-red-700">
          {siloError}
        </div>
      )}
      <TopBar
        currentTick={playback.currentTick}
        totalTicks={playback.totalTicks}
        finalMetrics={playback.finalMetrics}
        activeSpeed={playback.speed}
        playing={playback.playing}
        controlsDisabled={!playback.hasSimulation || playback.loading}
        onSelectSpeed={playback.setSpeed}
        onTogglePlay={playback.togglePlay}
        onAfterReset={() => {
          playback.reset();
          refetch();
          setStartModalOpen(true);
        }}
      />
      <YLevelSelector
        y={y}
        setY={setY}
        unlockAllLevels={playback.debugEnabled}
      />

      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 overflow-auto">
          <SiloCanvas
            silo={activeSilo}
            y={y}
            debugEnabled={playback.debugEnabled}
            highlightedPositions={playback.highlightedPositions}
            shuttleXByAisle={playback.shuttleXByAisle}
            selectedShuttle={selectedShuttle}
            onSelectSlot={selectSlot}
            onSelectShuttle={selectShuttle}
            onClearSelection={clearAllSelections}
          />
        </main>
        <RightPanel
          tab={tab}
          setTab={setTab}
          pallets={activePallets}
          events={activeEvents}
        />
      </div>

      <BottomBar
        actionMessage={playback.actionMessage}
        currentTick={playback.currentTick}
        totalTicks={playback.totalTicks}
        onSeek={playback.seek}
        scrubDisabled={!playback.hasSimulation || playback.loading}
      />

      <BoxTooltip slot={selectedSlot} onClose={clearBox} />

      {startModalOpen && (
        <StartModal
          onClose={() => setStartModalOpen(false)}
          onAfterRandomize={refetch}
          onStartSimulation={handleStartSimulation}
          simulationLoading={playback.loading}
          simulationError={playback.error}
        />
      )}
    </div>
  );
}
