import { useMemo, useState } from 'react'
import { BackendOfflineBanner } from './components/BackendOfflineBanner'
import { BottomBar } from './components/BottomBar'
import { BoxTooltip } from './components/BoxTooltip'
import { RightPanel } from './components/RightPanel'
import { SiloCanvas } from './components/SiloCanvas'
import { StartModal } from './components/StartModal'
import { TopBar } from './components/TopBar'
import { YLevelSelector } from './components/YLevelSelector'
import { useApi } from './hooks/useApi'
import { useBackendHealth } from './hooks/useBackendHealth'
import { usePalletSlots } from './hooks/usePalletSlots'
import { useRightPanelTab } from './hooks/useRightPanelTab'
import { useSelectedBox } from './hooks/useSelectedBox'
import { useSelectedShuttle } from './hooks/useSelectedShuttle'
import { useSiloState } from './hooks/useSiloState'
import { useYLevel } from './hooks/useYLevel'
import type { EventLogEntry } from './lib/types'

function App() {
  const { y, setY } = useYLevel()
  const { silo, refetch } = useSiloState()
  const { loading, error, setError, runRandomize, runReset } = useApi()
  const { selectedBox, selectBox, clearSelection } = useSelectedBox()
  const { selectedShuttle, setSelectedShuttle } = useSelectedShuttle()
  const { tab, setTab } = useRightPanelTab()
  const backendHealthy = useBackendHealth()
  const palletSlots = usePalletSlots()

  const [showModal, setShowModal] = useState(true)
  const [hasRandomized, setHasRandomized] = useState(false)
  const [showOfflineBanner, setShowOfflineBanner] = useState(true)
  const events: EventLogEntry[] = useMemo(() => [], [])

  async function handleRandomize(numBoxes: number) {
    await runRandomize(numBoxes)
    await refetch()
    setHasRandomized(true)
    setShowModal(false)
  }

  async function handleReset() {
    await runReset()
    await refetch()
    clearSelection()
    setSelectedShuttle(null)
  }

  async function handleUseMockData() {
    await refetch('/data/silo_setup_mock.csv')
    setHasRandomized(true)
    setShowModal(false)
    setError(null)
  }

  return (
    <div className="h-screen flex flex-col bg-bg-cream text-text-primary overflow-hidden">
      <BackendOfflineBanner
        visible={!backendHealthy && showOfflineBanner}
        onDismiss={() => setShowOfflineBanner(false)}
      />
      <TopBar onReset={handleReset} resetLoading={loading} />
      <YLevelSelector y={y} setY={setY} />

      <main className="flex-1 min-h-0 flex">
        <div className="flex-1 min-w-0">
          <SiloCanvas
            silo={silo}
            y={y}
            selectedShuttle={selectedShuttle}
            onSelectShuttle={setSelectedShuttle}
            onSelectBox={selectBox}
            onClearSelection={() => {
              clearSelection()
              setSelectedShuttle(null)
            }}
          />
        </div>
        <RightPanel tab={tab} setTab={setTab} palletSlots={palletSlots} events={events} />
      </main>

      <BottomBar disabled />

      {showModal && (
        <StartModal
          loading={loading}
          error={error}
          backendHealthy={backendHealthy}
          hasRandomized={hasRandomized}
          onRandomize={handleRandomize}
          onUseMockData={handleUseMockData}
        />
      )}

      {selectedBox && <BoxTooltip selected={selectedBox} onClose={clearSelection} />}
    </div>
  )
}

export default App
