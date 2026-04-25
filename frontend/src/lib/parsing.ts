import type { Box, Position, SiloState, Slot } from './types'

export function parsePositionString(s: string): Position {
  if (s.length !== 11 || !/^\d+$/.test(s)) {
    throw new Error(`Invalid position string: ${s}`)
  }

  const aisle = Number.parseInt(s.substring(0, 2), 10)
  const side = Number.parseInt(s.substring(2, 4), 10) as 1 | 2
  const x = Number.parseInt(s.substring(4, 7), 10)
  const y = Number.parseInt(s.substring(7, 9), 10)
  const z = Number.parseInt(s.substring(9, 11), 10) as 1 | 2

  return { aisle, side, x, y, z }
}

export function formatPositionString(p: Position): string {
  return `${p.aisle.toString().padStart(2, '0')}${p.side
    .toString()
    .padStart(2, '0')}${p.x.toString().padStart(3, '0')}${p.y
    .toString()
    .padStart(2, '0')}${p.z.toString().padStart(2, '0')}`
}

export function parseBoxId(s: string): Box {
  if (s.length !== 20 || !/^\d+$/.test(s)) {
    throw new Error(`Invalid box id: ${s}`)
  }

  return {
    box_id: s,
    source: s.substring(0, 7),
    destination: s.substring(7, 15),
    bulk: s.substring(15, 20),
  }
}

export function parseSiloCsv(csvText: string): SiloState {
  const silo: SiloState = new Map()
  const rows = csvText.split(/\r?\n/).filter((row) => row.trim().length > 0)

  for (let index = 1; index < rows.length; index += 1) {
    const [positionStr, boxId = ''] = rows[index].split(',')
    if (!positionStr) continue
    const position = parsePositionString(positionStr.trim())
    const slot: Slot = {
      position,
      box: boxId.trim() ? parseBoxId(boxId.trim()) : null,
    }
    silo.set(positionStr.trim(), slot)
  }

  return silo
}

export function getSlotsForY(silo: SiloState, y: number): Slot[] {
  return [...silo.values()]
    .filter((slot) => slot.position.y === y)
    .sort((a, b) => {
      const pa = a.position
      const pb = b.position
      return (
        pa.aisle - pb.aisle ||
        pa.side - pb.side ||
        pa.x - pb.x ||
        pa.z - pb.z
      )
    })
}

export function getSlotsForAisleSideY(
  silo: SiloState,
  aisle: number,
  side: 1 | 2,
  y: number,
): Slot[] {
  return [...silo.values()]
    .filter(
      (slot) =>
        slot.position.aisle === aisle &&
        slot.position.side === side &&
        slot.position.y === y,
    )
    .sort((a, b) => a.position.x - b.position.x || a.position.z - b.position.z)
}

// Example checks:
// parsePositionString("01010010101") => { aisle: 1, side: 1, x: 1, y: 1, z: 1 }
// parseBoxId("30557690100011012345").destination => "01000110"
