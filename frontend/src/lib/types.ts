export interface Position {
  aisle: number
  side: 1 | 2
  x: number
  y: number
  z: 1 | 2
}

export interface Box {
  box_id: string
  source: string
  destination: string
  bulk: string
}

export interface Slot {
  position: Position
  box: Box | null
}

export type SiloState = Map<string, Slot>

export interface PalletSlot {
  slot_id: number
  robot_id: 1 | 2
  destination: string | null
  filled: number
  capacity: 12
}

export interface EventLogEntry {
  t: number
  type: string
  message: string
}

export type RightPanelTab = 'pallets' | 'events'
