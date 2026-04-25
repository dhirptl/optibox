import { useCallback, useState } from "react";
import type { Box } from "../lib/types";

export function useSelectedBox() {
  const [selectedBox, setSelectedBox] = useState<Box | null>(null);
  const selectBox = useCallback((box: Box) => setSelectedBox(box), []);
  const clearSelection = useCallback(() => setSelectedBox(null), []);
  return { selectedBox, selectBox, clearSelection };
}
