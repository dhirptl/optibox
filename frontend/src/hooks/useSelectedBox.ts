import { useState } from 'react'
import type { Slot } from '../lib/types'

export interface SelectedBoxState {
  slot: Slot
  x: number
  y: number
}

export function useSelectedBox() {
  const [selectedBox, setSelectedBox] = useState<SelectedBoxState | null>(null)
  return {
    selectedBox,
    selectBox: (slot: Slot, x: number, y: number) => setSelectedBox({ slot, x, y }),
    clearSelection: () => setSelectedBox(null),
  }
}
