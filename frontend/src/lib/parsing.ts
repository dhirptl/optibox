import type { Position, Box, GridChange, Slot, SiloState } from "./types";

export function parsePositionString(s: string): Position {
  if (s.length !== 11) {
    throw new Error(`Position string must be 11 digits, got ${s.length}: "${s}"`);
  }
  const aisle = parseInt(s.slice(0, 2), 10);
  const side = parseInt(s.slice(2, 4), 10);
  const x = parseInt(s.slice(4, 7), 10);
  const y = parseInt(s.slice(7, 9), 10);
  const z = parseInt(s.slice(9, 11), 10);
  return {
    aisle,
    side: side as 1 | 2,
    x,
    y,
    z: z as 1 | 2,
  };
}

export function formatPositionString(p: Position): string {
  return (
    p.aisle.toString().padStart(2, "0") +
    p.side.toString().padStart(2, "0") +
    p.x.toString().padStart(3, "0") +
    p.y.toString().padStart(2, "0") +
    p.z.toString().padStart(2, "0")
  );
}

export function parseBoxId(s: string): Box {
  if (s.length !== 20) {
    throw new Error(`Box id must be 20 digits, got ${s.length}: "${s}"`);
  }
  return {
    box_id: s,
    source: s.slice(0, 7),
    destination: s.slice(7, 15),
    bulk: s.slice(15, 20),
  };
}

export function parseSiloCsv(csvText: string): SiloState {
  const silo: SiloState = new Map();
  const lines = csvText.split(/\r?\n/);
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i]?.trim();
    if (!line) continue;
    const [rawPosicion, rawEtiqueta = ""] = line.split(",", 2);
    const posicion = rawPosicion?.trim();
    const etiqueta = rawEtiqueta.trim();
    if (!posicion) continue;
    const position = parsePositionString(posicion);
    const slot: Slot = {
      position,
      box: etiqueta ? parseBoxId(etiqueta) : null,
    };
    silo.set(posicion, slot);
  }
  return silo;
}

export function getSlotsForY(silo: SiloState, y: number): Slot[] {
  const result: Slot[] = [];
  for (const slot of silo.values()) {
    if (slot.position.y === y) result.push(slot);
  }
  return result;
}

export function getSlotsForAisleSideY(
  silo: SiloState,
  aisle: number,
  side: 1 | 2,
  y: number,
): Slot[] {
  const result: Slot[] = [];
  for (const slot of silo.values()) {
    const p = slot.position;
    if (p.aisle === aisle && p.side === side && p.y === y) {
      result.push(slot);
    }
  }
  return result;
}

export function cloneSiloState(source: SiloState): SiloState {
  const next: SiloState = new Map();
  for (const [key, slot] of source.entries()) {
    next.set(key, {
      position: { ...slot.position },
      box: slot.box ? { ...slot.box } : null,
    });
  }
  return next;
}

export function applyGridChangesForward(silo: SiloState, changes: GridChange[]): SiloState {
  const next = cloneSiloState(silo);
  applyGridChangesForwardInPlace(next, changes);
  return next;
}

export function applyGridChangesBackward(silo: SiloState, changes: GridChange[]): SiloState {
  const next = cloneSiloState(silo);
  applyGridChangesBackwardInPlace(next, changes);
  return next;
}

export function applyGridChangesForwardInPlace(silo: SiloState, changes: GridChange[]): void {
  for (const change of changes) {
    upsertSlot(silo, change.position, change.after);
  }
}

export function applyGridChangesBackwardInPlace(silo: SiloState, changes: GridChange[]): void {
  for (const change of changes) {
    upsertSlot(silo, change.position, change.before);
  }
}

function upsertSlot(silo: SiloState, positionKey: string, box: Box | null): void {
  const existing = silo.get(positionKey);
  if (existing) {
    silo.set(positionKey, {
      ...existing,
      box: box ? { ...box } : null,
    });
    return;
  }

  silo.set(positionKey, {
    position: parsePositionString(positionKey),
    box: box ? { ...box } : null,
  });
}
