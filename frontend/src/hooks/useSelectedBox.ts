import { useCallback, useState } from "react";
import type { Slot } from "../lib/types";

export function useSelectedBox() {
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const selectSlot = useCallback((slot: Slot) => setSelectedSlot(slot), []);
  const clearSelection = useCallback(() => setSelectedSlot(null), []);
  return { selectedSlot, selectSlot, clearSelection };
}
