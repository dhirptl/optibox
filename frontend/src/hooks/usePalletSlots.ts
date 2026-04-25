import { useMemo } from 'react'
import type { PalletSlot } from '../lib/types'

export function usePalletSlots() {
  return useMemo<PalletSlot[]>(
    () =>
      Array.from({ length: 8 }, (_, i) => ({
        slot_id: i + 1,
        robot_id: i < 4 ? 1 : 2,
        destination: null,
        filled: 0,
        capacity: 12,
      })),
    [],
  )
}
