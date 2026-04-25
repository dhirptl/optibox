import { useState } from 'react'
import type { RightPanelTab } from '../lib/types'

export function useRightPanelTab() {
  const [tab, setTab] = useState<RightPanelTab>('pallets')
  return { tab, setTab }
}
