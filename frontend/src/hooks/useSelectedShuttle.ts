import { useState } from 'react'

export interface SelectedShuttle {
  aisle: number
  y: number
  current_x: number
}

export function useSelectedShuttle() {
  const [selectedShuttle, setSelectedShuttle] = useState<SelectedShuttle | null>(
    null,
  )
  return { selectedShuttle, setSelectedShuttle }
}
